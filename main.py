"""
Main pipeline for generating GraphQL queries for Tableau Metadata API.
Uses Neo4j schema store + LLM orchestration + validation/correction.
"""

from utils.neo4j_store import (
    check_env_vars, init_graph_driver, is_graph_built,
    build_graph, get_schema_types, get_schema_snippet, get_schema_paths,
    validate_query
)
from utils.llm_orchestration import (
    check_llm_env_vars, get_llm,
    infer_types_from_intent, parse_types,
    graphql_prompt, extract_query_and_vars, build_correction_prompt
)
from utils.validation import extract_invalids


def generate_graphql_with_inference(user_intent, max_hops=5, max_retries=2):
    """
    Generate a valid GraphQL query from a natural language user intent.
    Pipeline:
      1. Check env vars & init graph
      2. Infer src/dst types from intent
      3. Retrieve schema paths
      4. Get schema snippet(s)
      5. Prompt LLM
      6. Extract query/variables
      7. Validate
      8. Retry with correction loop if needed
    """

    # -----------------------------
    # Step 0: Check environment vars
    # -----------------------------
    check_env_vars()       # Neo4j + LLM variables exist
    check_llm_env_vars()   # LLM specific variables

    # -----------------------------
    # Step 1: Init Neo4j graph
    # -----------------------------
    graph = init_graph_driver()

    # If no schema loaded, prompt rebuild
    if not is_graph_built(graph):
        status = build_graph(graph)
        if not status:
            raise RuntimeError("Error Building schema graph.")

    # -----------------------------
    # Step 2: Infer source/destination types
    # -----------------------------
    schema_types = get_schema_types(graph)
    llm = get_llm()
    inferred = infer_types_from_intent(llm, user_intent, schema_types)
    src_type, dst_type = parse_types(inferred)

    # -----------------------------
    # Step 3: Retrieve schema paths
    # -----------------------------
    paths = get_schema_paths(graph, src_type, dst_type, max_hops=max_hops)
    if not paths:
        return {"error": f"No valid schema path found between {src_type} and {dst_type}"}

    schema_path = "\n".join([
        " -> ".join(p['nodes']) + " via " + " -> ".join(p['fields'])
        for p in paths
    ])

    # -----------------------------
    # Step 4: Get schema snippets
    # -----------------------------
    schema_snippets = get_schema_snippet(graph, src_type)

    # -----------------------------
    # Step 5: Build initial prompt & call LLM
    # -----------------------------
    prompt = graphql_prompt.format(
        user_intent=user_intent,
        schema_path=schema_path,
        schema_snippets=schema_snippets
    )
    response = llm.predict(prompt)

    # -----------------------------
    # Step 6: Extract query & variables
    # -----------------------------
    query, variables = extract_query_and_vars(response)
    if not query:
        return {"error": "Invalid LLM output", "raw": response}

    # -----------------------------
    # Step 7: Validate query
    # -----------------------------
    errors = validate_query(query)

    # -----------------------------
    # Step 8: Correction loop
    # -----------------------------
    retries = 0
    while errors and retries < max_retries:
        invalids = extract_invalids([str(e) for e in errors])

        # Build map of allowed fields from Neo4j
        allowed_fields_map = {
            inv["type"]: [
                row["field"] for row in graph.query(
                    """
                    MATCH (t:Type {name:$t})-[:HAS_FIELD]->(f:Field)
                    RETURN f.name as field
                    """,
                    params={"t": inv["type"]}
                )
            ]
            for inv in invalids
        }

        # Correction prompt
        correction_prompt = build_correction_prompt(
            user_intent, query, invalids, allowed_fields_map
        )

        # Retry LLM
        response = llm.predict(correction_prompt)
        query, variables = extract_query_and_vars(response)
        if not query:
            return {"error": "Correction step failed", "raw": response}

        errors = validate_query(query)
        retries += 1

    # -----------------------------
    # Step 9: Return final result
    # -----------------------------
    if errors:
        return {"query": query, "variables": variables, "errors": [str(e) for e in errors]}

    print("✅ Final Query:\n", query)
    print("\nVariables:", variables, "\n")

    return {"query": query, "variables": variables, "errors": {}}


if __name__ == "__main__":
    import sys
    import os

    # -------------------------
    # 1. Load environment variables
    # -------------------------
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        print("⚠️ python-dotenv not installed. Make sure environment variables are set manually.")

    # -------------------------
    # 2. Check for required env vars
    # -------------------------
    try:
        check_env_vars()
        check_llm_env_vars()
    except EnvironmentError as e:
        print(f"❌ Missing environment variable: {e}")
        sys.exit(1)

    # -------------------------
    # 3. Get user intent from CLI arg
    # -------------------------
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<user_intent>\"")
        sys.exit(1)

    user_intent = sys.argv[1]

    # -------------------------
    # 4. Run pipeline
    # -------------------------
    print(f"\n🤖 Generating GraphQL query for intent: {user_intent}\n")
    result = generate_graphql_with_inference(user_intent)

    # -------------------------
    # 5. Print results
    # -------------------------
    if "error" in result and result["error"]:
        print("❌ Error:", result["error"])
        if "raw" in result:
            print("Raw LLM response:", result["raw"])
    else:
        print("✅ Final Query:\n", result["query"])
        print("\n📦 Variables:\n", result["variables"])
        if result.get("errors"):
            print("\n⚠️ Validation Errors:\n", result["errors"])
        else:
            print("\n✨ Query validated successfully!")
