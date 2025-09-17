import gradio as gr
import os
import requests
from dotenv import load_dotenv

# Import pipeline
from main import generate_graphql_with_inference
from utils.neo4j_store import check_env_vars
from utils.llm_orchestration import check_llm_env_vars

# -------------------------
# Load .env file
# -------------------------
load_dotenv(override=True)
check_env_vars()
check_llm_env_vars()


# -------------------------
# Inference wrapper
# -------------------------
def run_inference(user_intent):
    result = generate_graphql_with_inference(user_intent)

    query = result.get("query")
    variables = result.get("variables", {})
    errors = "\n".join(result.get("errors", [])) if result.get("errors") else "✅ No validation errors"

    return user_intent, query, variables, errors


def execute_curl(query, variables, endpoint, token):
    if not endpoint or not token or not query:
        return {"error": "⚠️ Missing endpoint, token, or query."}

    try:
        resp = requests.post(
            endpoint + '/api/metadata/graphql',
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            },
            json={"query": query, "variables": variables}
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"❌ Failed to run query: {e}"}


# -------------------------
# Elite Gradio UI
# -------------------------
with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="violet")) as demo:
    gr.Markdown(
    """
    <div style="text-align: center; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <h1 style="font-size: 3em; font-weight: 800;
                   background: linear-gradient(90deg, #4f46e5, #9333ea, #ec4899, #f59e0b);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   display: inline-flex;
                   align-items: center;
                   gap: 0.5em;">
            🕸️ GraphWeaver
        </h1>
        <p style="font-size: 1.2em; color: #6b7280; margin-top: -10px;">
            Weaving user intent into valid Tableau GraphQL queries
        </p>
    </div>
    """
    )

    gr.Markdown(
        """
        # ⚡️ GraphQL Query Generator for Tableau Metadata API  
        *Elite Assistant for Analysts & Engineers*  
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            user_input = gr.Textbox(
                label="📝 What do you want to get?",
                placeholder="e.g. Get all workbooks owned by user Jane Doe",
                lines=3
            )
            run_btn = gr.Button("🚀 Generate Query", variant="primary")

            with gr.Accordion("⚙️ Run Query via cURL (Optional)", open=False):
                endpoint_url = gr.Textbox(
                    label="Tableau Domain",
                    placeholder="https://your-tableau-server",
                )
                auth_token = gr.Textbox(
                    label="Bearer Token",
                    placeholder="Paste your Tableau personal access token",
                    type="password",
                )
                curl_btn = gr.Button("🌐 Execute Query via cURL", variant="secondary")

        with gr.Column(scale=2):
            with gr.Accordion("📜 Generated GraphQL Query", open=True):
                query_out = gr.Code(label="GraphQL Query", language="sql")

            with gr.Accordion("📦 Variables", open=False):
                vars_out = gr.JSON(label="Variables")

            with gr.Accordion("🛠️ Validation Results", open=False):
                errors_out = gr.Textbox(label="Errors / Status", interactive=False)

            with gr.Accordion("🌐 Query Response (Optional)", open=False):
                curl_out = gr.JSON(label="cURL Response")

    # Generate query
    run_btn.click(
        fn=run_inference,
        inputs=[user_input],
        outputs=[user_input, query_out, vars_out, errors_out]
    )

    # Execute curl
    curl_btn.click(
        fn=execute_curl,
        inputs=[query_out, vars_out, endpoint_url, auth_token],
        outputs=[curl_out]
    )

    gr.Markdown(
        """
        ---
        🔒 **Notes:**  
        - First generate a query with **🚀 Generate Query**.  
        - Then optionally execute it with **🌐 Execute Query via cURL** (requires endpoint + token).  
        """
    )


# -------------------------
# Run app
# -------------------------
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
