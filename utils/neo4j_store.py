import os
from langchain_community.graphs import Neo4jGraph
from graphql import build_schema, parse, validate, build_client_schema
import json

# -----------------------------
# 1. Check required environment variables
# -----------------------------
def check_env_vars(required_vars=None):
    """
    Check if required environment variables are set.
    Returns a dict of {var: value} if all are valid, else raises ValueError.
    """
    if required_vars is None:
        required_vars = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return {var: os.getenv(var) for var in required_vars}


# -----------------------------
# 2. Instantiate Neo4j driver and graph session
# -----------------------------
def init_graph_driver():
    """
    Initialize Neo4j driver using env vars.
    Returns a Neo4j driver object.
    """
    env = check_env_vars(["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD"])
    uri = env["NEO4J_URI"]
    user = env["NEO4J_USER"]
    password = env["NEO4J_PASSWORD"]

    graph = Neo4jGraph(
    url=uri,
    username=user,
    password=password
)
    return graph


# -----------------------------
# 3. Check if schema graph already built
# -----------------------------
def is_graph_built(graph, rebuild: bool = False) -> bool:
    """
    Check if the schema graph has been built in Neo4j.
    Uses the Neo4jGraph object instead of raw driver.
    
    Args:
        graph: Neo4jGraph object
        rebuild (bool): If True, clears the graph and returns False.

    Returns:
        bool: True if schema graph exists, False otherwise.
    """
    if rebuild:
        graph.query("MATCH (n) DETACH DELETE n")
        return False  # Graph cleared, needs rebuild

    result = graph.query("MATCH (n) RETURN count(n) as count")
    count = result[0]["count"] if result else 0
    return count > 0


# -----------------------------
# 4. Build graph schema
# -----------------------------
def build_graph(graph):
    """
    Build Neo4g Graph based on schema.graphql file
    """
    with open("./schema/schema.graphql", "r", encoding="utf-8") as f:
        sdl = f.read()
        schema = build_schema(sdl)
        type_map = schema.type_map

    with graph as graph:
        for type_name, gql_type in type_map.items():
            if type_name.startswith("__") or not hasattr(gql_type, "fields"):
                continue

            # Create Type node
            graph.query("MERGE (t:Type {name:$name})", name=type_name)

            # Loop over fields
            for field_name, field in gql_type.fields.items():
                field_type = str(field.type).replace("!", "").replace("[", "").replace("]", "")

                # Create Field node
                graph.query("""
                    MERGE (f:Field {name:$fname, parentType:$tname})
                    MERGE (t:Type {name:$tname})
                    MERGE (t)-[:HAS_FIELD]->(f)
                """, fname=field_name, tname=type_name)

                # If field refers to another Type, add relationship
                if field_type in type_map:
                    graph.query("""
                        MERGE (src:Type {name:$src})
                        MERGE (dst:Type {name:$dst})
                        MERGE (src)-[:HAS_RELATION {field:$fname}]->(dst)
                    """, src=type_name, dst=field_type, fname=field_name)

    # check graoh status
    status = is_graph_built(graph, rebuild = False)
    return status


# -----------------------------
# 5. Get Available Schema Types
# -----------------------------
def get_schema_types(graph):
    schema_types = [t["name"] for t in graph.query("MATCH (t:Type) RETURN t.name as name")]
    return schema_types

# -----------------------------
# 5. Extract schema snippets
# -----------------------------
def get_schema_snippet(graph, type_name: str) -> str:
    """
    Fetch schema snippet for a given type from Neo4j.
    """
    cypher = """
    MATCH (t:Type {name:$type})-[:HAS_FIELD]->(f:Field)
    OPTIONAL MATCH (t)-[r:HAS_RELATION]->(dst:Type)
    WHERE r.field = f.name
    RETURN f.name as field, dst.name as dstType
    ORDER BY f.name
    """
    results = graph.query(cypher, params={"type": type_name})

    snippet = [f"type {type_name} {{"]
    for row in results:
        if row["dstType"]:
            # relation to another Type
            snippet.append(f"  {row['field']}: [{row['dstType']}]")
        else:
            # scalar field
            snippet.append(f"  {row['field']}")
    snippet.append("}")

    return "\n".join(snippet)

# -----------------------------
# 6. Get paths
# -----------------------------
def get_schema_paths(graph, src, dst, max_hops=5):
    cypher = f"""
    MATCH p = shortestPath((src:Type {{name:'{src}'}})-[:HAS_RELATION*..{max_hops}]->(dst:Type {{name:'{dst}'}}))
    RETURN [n in nodes(p) | n.name] as nodes, [r in relationships(p) | r.field] as fields
    """
    res = graph.query(cypher)
    return res

# -----------------------------
# 2. Validate a GraphQL query
# -----------------------------
def validate_query(query: str):
    """
    Validate a GraphQL query string against the schema.
    Returns list of error messages (empty if valid).
    """
    with open("./schema/schema.json") as f:
        data = json.load(f)

    schema = build_client_schema(data)
    try:
        ast = parse(query)
        errors = validate(schema, ast)
        return [str(err) for err in errors]
    except Exception as e:
        return [f"Parsing/validation error: {e}"]