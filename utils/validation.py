from utils.neo4j_store import validate_query
from graphql import parse, validate, GraphQLSchema
import json
import re




# -----------------------------
# 3. Pretty print validation errors
# -----------------------------
def print_validation_result(query: str, schema: GraphQLSchema):
    """
    Run validation and print results nicely.
    """
    errors = validate_query(query, schema)
    if not errors:
        print("✅ Query is valid.")
    else:
        print("❌ Query has errors:")
        for err in errors:
            print(f" - {err}")

# -----------------------------
# 6. Re-prompt LLM with feedback
# -----------------------------
def extract_invalids(errors):
    # errors is a list of GraphQL error messages
    invalid = []
    for e in errors:
        m = re.search(r"Cannot query field '([^']+)' on type '([^']+)'", e)
        if m:
            invalid.append({"field": m.group(1), "type": m.group(2)})
    return invalid