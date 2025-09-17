# ⚡ GraphWeaver

<p align="center">
  <img src="https://img.shields.io/badge/GraphQL-Query%20Generator-blueviolet?style=for-the-badge&logo=graphql" alt="GraphQL Badge"/>
  <img src="https://img.shields.io/badge/Tableau-Metadata%20API-orange?style=for-the-badge&logo=tableau" alt="Tableau Badge"/>
  <img src="https://img.shields.io/badge/Neo4j-Knowledge%20Graph-teal?style=for-the-badge&logo=neo4j" alt="Neo4j Badge"/>
</p>

## 🎯 Purpose

**GraphWeaver** is an AI-powered assistant that transforms **plain English user intents** into **valid GraphQL queries** for the **Tableau Metadata API**.
It leverages **Neo4j as a schema graph** and an **LLM for query orchestration**, enabling analysts and engineers to interact with Tableau metadata without needing deep GraphQL knowledge.

---

## 🌟 Benefits

* ✅ **Natural Language to GraphQL** – write “Get all dashboards for workbook *Sales*” and let GraphWeaver build the query.
* ✅ **Schema-Aware** – ensures generated queries respect Tableau’s Metadata API schema.
* ✅ **Validation & Correction** – automatically validates queries and retries corrections if needed.
* ✅ **Neo4j-powered** – schema relationships are stored as a graph for accurate traversal.
* ✅ **Optional cURL Execution** – test queries directly from the UI against your Tableau Metadata API.
* ✅ **Accessible UI** – powered by **Gradio**, with a modern, elite design.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    A([User Input: Natural Language Intent]) --> B([Gradio UI])
    B --> C([GraphWeaver Engine - Python])
    C --> D([Neo4j Schema Graph])
    C --> E([LLM - OpenAI / Local Model])
    C --> F([GraphQL Query Builder])
    F --> G([Tableau Metadata API])
    G --> B

    %% Styling
    classDef user fill:#ffcc00,stroke:#333,stroke-width:2px,color:#000;
    classDef ui fill:#66ccff,stroke:#333,stroke-width:2px,color:#000;
    classDef engine fill:#ff99cc,stroke:#333,stroke-width:2px,color:#000;
    classDef db fill:#99ff99,stroke:#333,stroke-width:2px,color:#000;
    classDef llm fill:#cc99ff,stroke:#333,stroke-width:2px,color:#000;
    classDef query fill:#ff9966,stroke:#333,stroke-width:2px,color:#000;
    classDef api fill:#cccccc,stroke:#333,stroke-width:2px,color:#000;

    class A user;
    class B ui;
    class C engine;
    class D db;
    class E llm;
    class F query;
    class G api;
```

* **Neo4j Schema Graph**: Stores GraphQL schema structure (types, fields, relations).
* **LLM**: Interprets user intent and generates candidate queries.
* **Validator**: Ensures query matches the schema and applies correction loops if needed.
* **UI**: Provides query output, error messages, and optional cURL execution.

---

## 🚀 Setup (Python Environment)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/graphweaver.git
cd graphweaver
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yourpassword

LLM_API_KEY=your-openai-or-local-llm-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

### 5. Run the app

```bash
python app.py
```

App will be available at: 👉 [http://localhost:7860](http://localhost:7860)

---

## 🐳 Setup (Docker)

### 1. Build the container

```bash
docker build -t graphweaver .
```

### 2. Run with environment file

```bash
docker run -it --rm -p 7860:7860 --env-file .env graphweaver
```

Or with **docker-compose**:

```bash
docker-compose up --build
```

---

## 🧑‍💻 Example Usage

* **User Input**:
  *“List all workbooks by name and ID.”*

* **GraphWeaver Output**:

  ```graphql
  query MyQuery {
    workbooksConnection(first: 10) {
      nodes {
        id
        name
      }
    }
  }
  ```

* **Optional cURL Execution**:
  Configure Tableau GraphQL endpoint in the UI and run the query directly.

---

## 📌 Roadmap

* [ ] Support multiple LLM backends (OpenAI, local models, Azure).
* [ ] Add schema visualization in UI (Neo4j → Network graph).
* [ ] Enhance retry logic with more advanced error correction.

---

## 📜 License

MIT License © 2025 – Made with ❤️ for analysts & engineers