from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
import os
import re

# -----------------------------
# 1. Check LLM env vars
# -----------------------------
def check_llm_env_vars(required_vars=None):
    """
    Check if LLM-related environment variables are set.
    Returns a dict {var: value} if valid, else raises ValueError.
    """
    if required_vars is None:
        required_vars = ["LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"]

    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required LLM environment variables: {', '.join(missing)}")

    return {var: os.getenv(var) for var in required_vars}


# -----------------------------
# 2. Get LLM instance
# -----------------------------
def get_llm(temperature: float = 0.0):
    """
    Initialize and return an LLM object (ChatOpenAI) using env vars.
    """
    env = check_llm_env_vars()

    llm = ChatOpenAI(
        api_key=env["LLM_API_KEY"],
        base_url=env["LLM_BASE_URL"],
        model=env["LLM_MODEL"],
        temperature=temperature
    )
    return llm


# -----------------------------
# 3. Infer Scema Types
# -----------------------------
def infer_types_from_intent(llm, user_intent, schema_types):
    schema_str = ", ".join(schema_types)
    prompt = f"""
You are a schema type resolver.
Available schema types: {schema_str}.

User request: "{user_intent}"

If a type has both a direct entity (Dashboard) and a Connection type (DashboardsConnection),
always prefer the base entity type (Dashboard).

Return the most relevant source type and destination type
from the schema (JSON format with keys 'src_type' and 'dst_type').
"""
    resp = llm.predict(prompt)
    return resp


# -----------------------------
# 4. Parse Types
# -----------------------------
def parse_types(llm_response: str):
    # Extract the first JSON object (even if wrapped in ```json ... ```)
    match = re.search(r'\{.*\}', llm_response, re.DOTALL)
    if not match:
        return None, None

    cleaned = match.group(0)  # just the {...}
    data = json.loads(cleaned)

    return data.get("src_type"), data.get("dst_type")


# -----------------------------
# 5. Prompt Template
# -----------------------------
graphql_prompt = PromptTemplate(
    input_variables=["user_intent", "schema_path", "schema_snippets"],
    template="""
You are a Tableau GraphQL query generator.
Your job is to produce a VALID GraphQL query for Tableau’s Metadata API.

### User intent:
{user_intent}

### Schema path:
{schema_path}

### Allowed schema snippets (ground truth):
{schema_snippets}

### STRICT RULES:
1. Only use fields shown in the schema snippets above. Never invent fields or relations.
2. Follow the schema path exactly — do not guess or insert missing links.
3. Always use plural root fields from type Query (e.g., `workbooks`, `datasources`, `databaseTables`, `tableauUsers`).

4. Filtering:
   - Allowed only on scalar fields explicitly listed in `<Type>_Filter`.
   - Do NOT use relationship fields inside filters.
   - Do NOT invent operators like `contains` unless shown in the filter type.
   - If the user intent requires filtering on a non-filterable field, return exactly:
     `No valid path`.

5. Connection vs List:
   - If a field ends with `Connection`, use the pattern:
     `connectionName(first: N) {{ nodes {{ ...fields }} }}`
   - If a field is a plain list (`[Type!]!`), query the items directly without `nodes`.
   - Never add pagination args (`first:`, `after:`) to plain lists.

6. Sorting:
   - Only use `orderBy:` if the schema snippet explicitly shows it.
   - Syntax: `orderBy: {{field: NAME, direction: ASC}}`.

7. Nested connections:
   - Query nested connections (e.g., `downstreamSheetsConnection`, `upstreamTablesConnection`) only from their parent type.
   - Never query them directly at the root.

8. Calculated fields:
   - Retrieve via `fields` or `calculatedFields` under `Datasource`.
   - Never use `worksheetFieldsConnection`.

9. Always request a few scalar fields (`id`, `name`, etc.) at each level for clarity.

10. If the user intent is a simple list (e.g., "list all X with id and name"), 
    only query the root type (no traversal into relationships).

11. If no valid query can be built with the schema snippets, respond exactly:
    `No valid path`

### Output format:
  - Always wrap the query in fenced code block:
  ```graphql
  query MyQuery {{ <your query here> }}
  ```

  - Variables (if any) must be valid JSON, wrapped in:

  ```json
  {{ <your variables here> }}
  ```
"""
)

# -----------------------------
# 6. Re-prompt LLM with feedback
# -----------------------------
def extract_query_and_vars(response: str):
    # Look for fenced GraphQL block
    match = re.search(r"```graphql(.*?)```", response, re.S)
    if match:
        query = match.group(1).strip()
    else:
        # Fallback: try "GraphQL Query:" section
        match = re.search(r"GraphQL Query:\s*(.*?)\n\nVariables:", response, re.S)
        query = match.group(1).strip() if match else None

    # Extract variables block
    match_vars = re.search(r"Variables:\s*```json(.*?)```", response, re.S)
    if match_vars:
        try:
            variables = json.loads(match_vars.group(1).strip())
        except:
            variables = {}
    else:
        match_vars = re.search(r"Variables:\s*(\{.*\})", response, re.S)
        try:
            variables = json.loads(match_vars.group(1).strip())
        except:
            variables = {}

    return query, variables

# -----------------------------
# 6. Build Correction Prompt
# -----------------------------
def build_correction_prompt(intent, original_query, invalids, allowed_fields_map):
    # allowed_fields_map: {"Database": ["id","name","host",...], ...}
    lines = [
      "The previously generated GraphQL query failed validation.",
      f"User intent: {intent}",
      f"Original query:\n```graphql\n{original_query}\n```"
    ]
    for inv in invalids:
        t = inv["type"]
        lines.append(f"Error: field '{inv['field']}' is not allowed on type '{t}'.")
        lines.append(f"Allowed fields for {t}: {', '.join(allowed_fields_map[t])}")
        lines.append("Please regenerate the query using only allowed fields. Prefer id and name where appropriate.")
    lines.append("Return only the corrected query in a ```graphql ... ``` block and variables in ```json ... ```.")
    return "\n\n".join(lines)
