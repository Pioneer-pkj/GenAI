# 🌍 Population Census Chatbot

An AI-powered chatbot that answers population-related questions using **Google ADK (Agent Development Kit)**, **Gemini 3.5 Flash**, and **BigQuery** as the data source — with a **Streamlit** conversational UI.

---

## 📁 Project Structure

```
population_census/
├── agent.py              # ADK agent definition (backend brain)
├── agent_callback.py     # Before/after agent callbacks (access control & logging)
├── chatbot_ui.py         # Streamlit chatbot frontend
├── __init__.py           # Python package marker
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker image for Cloud Run deployment
├── .dockerignore         # Files excluded from Docker image
├── .env                  # Local environment variables (not deployed)
└── .gitignore            # Git ignore rules
```

---

## 🧠 Backend — ADK Agent (`agent.py`)

The backend is built using **Google ADK** and defines an intelligent agent that:

- Uses **Gemini 3.5 Flash** as the LLM model
- Connects to **BigQuery** via `BigQueryToolset` to query the `gcai-sep-26.Popluation_census.global_population` table
- Formats responses in bullet points / tabular format
- Politely refuses non-population-related questions

### Key Components

| Component | Description |
|---|---|
| `root_agent` | The main `Agent` with model, instructions, and tools |
| `bigquery_toolset` | Provides BigQuery read/write tools to the agent |
| `bigquery_tool_config` | Configures BigQuery write mode (`ALLOWED`) |
| `logging_plugin` | Logs all agent interactions (requests, responses, tool calls) |
| `bq_plugin` | `BigQueryAgentAnalyticsPlugin` — stores agent analytics in BigQuery |
| `app` | The ADK `App` that wraps the agent with plugins |

### Agent Callbacks (`agent_callback.py`)

Two lifecycle callbacks are attached to the agent:

#### `check_access` — Before Agent Callback
- Runs **before** every agent invocation
- Validates the `user_id` against an allow-list (`['pankaj', 'user']`)
- Returns `None` to proceed, or a denial `Content` to block unauthorized users

#### `log_completion` — After Agent Callback
- Runs **after** every agent invocation
- Extracts and prints:
  - ⏱️ Time consumed (seconds)
  - 🔢 Token usage breakdown (prompt, candidate, thoughts)

### Environment Variables (`.env`)

```env
GOOGLE_GENAI_USE_ENTERPRISE=1       # Use Vertex AI (enterprise) backend
GOOGLE_CLOUD_PROJECT=gcai-sep-26    # GCP project ID
GOOGLE_CLOUD_LOCATION=global        # API location
```

---

## 💬 Frontend — Streamlit Chatbot (`chatbot_ui.py`)

A conversational chat interface built with **Streamlit** that connects to the ADK agent locally via `InMemoryRunner`.

### Features

| Feature | Description |
|---|---|
| 💬 **Chat Interface** | Full conversational UI with persistent chat history |
| 📋 **Sample Questions** | 8 pre-built clickable questions in the sidebar |
| 🔢 **Token Tracking** | Displays total / prompt / output token usage per response |
| 👤 **User Switching** | Text input to change User ID (tests access control callback) |
| 🗑️ **Clear Conversation** | Reset button to start a fresh session |
| 🎨 **Custom Styling** | Gradient header, Inter font, themed buttons, token badges |

### How It Works

1. **Agent Loading** — Imports the ADK `App` from `agent.py`
2. **Runner** — Creates an `InMemoryRunner` (cached via `@st.cache_resource`)
3. **Session** — Creates an ADK session per user via `create_session_sync()`
4. **Messaging** — Converts user input to `types.Content`, calls `runner.run()`, and extracts text + token metadata from events
5. **Rendering** — Displays messages in Streamlit's `st.chat_message` containers

### Architecture Flow

```
User Input → Streamlit UI → InMemoryRunner → ADK Agent
                                                  ↓
                                          check_access (callback)
                                                  ↓
                                          Gemini 3.5 Flash (LLM)
                                                  ↓
                                          BigQuery Toolset (SQL)
                                                  ↓
                                          log_completion (callback)
                                                  ↓
                                          Response → Streamlit UI
```

---

## 🚀 Running Locally

### Prerequisites

- Python 3.11+
- Google Cloud SDK authenticated (`gcloud auth application-default login`)
- BigQuery access to `gcai-sep-26.Popluation_census.global_population`

### Steps

```bash
# 1. Navigate to the Plugins directory (parent of population_census)
cd /path/to/GenAI/Plugins

# 2. Install dependencies
pip install -r population_census/requirements.txt

# 3. Run the Streamlit chatbot
streamlit run population_census/chatbot_ui.py
```

The app will open at **http://localhost:8501**

---

## ☁️ Deploying to Google Cloud Run

### Option 1: Deploy the ADK Agent (with built-in ADK Web UI)

This uses the `adk deploy` CLI which includes a development-purpose web UI:

```bash
cd /path/to/GenAI/Plugins

adk deploy cloud_run \
  --service_name="population-census-ui" \
  --project=gcai-sep-26 \
  --with_ui \
  --region=asia-south1 \
  population_census
```

> ⚠️ The ADK Web UI is for **development purposes only** and should not be used in production.

### Option 2: Deploy the Streamlit Chatbot UI

This deploys the custom Streamlit chatbot with the Dockerfile:

```bash
# IMPORTANT: Run from inside the population_census directory
cd /path/to/GenAI/Plugins/population_census

gcloud run deploy population-census-chatbot \
  --source . \
  --project gcai-sep-26 \
  --region asia-south1 \
  --set-env-vars "GOOGLE_GENAI_USE_ENTERPRISE=1,GOOGLE_CLOUD_PROJECT=gcai-sep-26,GOOGLE_CLOUD_LOCATION=global" \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300
```

### Deployment Flags Explained

| Flag | Purpose |
|---|---|
| `--source .` | Builds the Docker image from `Dockerfile` in the current directory via Cloud Build |
| `--set-env-vars` | Injects environment variables (replaces `.env` which is excluded from Docker image) |
| `--allow-unauthenticated` | Makes the UI publicly accessible (remove for private access) |
| `--memory 1Gi` | ADK + Streamlit require more than the default 512MB |
| `--timeout 300` | Allows up to 5 minutes for BigQuery queries to complete |

### IAM Requirements

The Cloud Run service account needs these roles on the `gcai-sep-26` project:

| Role | Purpose |
|---|---|
| `roles/bigquery.dataViewer` | Read access to BigQuery tables |
| `roles/bigquery.jobUser` | Permission to run BigQuery queries |
| `roles/aiplatform.user` | Access to Vertex AI / Gemini models |

### Dockerfile Overview

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./population_census/
EXPOSE 8080
CMD streamlit run population_census/chatbot_ui.py \
    --server.port=${PORT:-8080} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
```

- Copies the entire `population_census/` package into `/app/population_census/`
- Uses Cloud Run's `PORT` environment variable (defaults to 8080)
- Runs Streamlit in headless mode (no browser auto-open)

---

## 📦 Dependencies (`requirements.txt`)

```
google-cloud-bigquery-storage
google-cloud-bigquery
google-cloud-storage
google-adk[bigquery-analytics]
google-adk[gcs-storage-plugin]
pyarrow
streamlit
python-dotenv
```

---

## 🔐 Access Control

The chatbot includes a simple role-based access control via the `check_access` callback:

- **Authorized users**: `pankaj`, `user`
- **Unauthorized users** receive: _"You do not have access to HR Agent, user {user_id} is not in HR team"_
- The User ID can be changed from the sidebar in the Streamlit UI

---

## 📊 Data Source

- **Project**: `gcai-sep-26`
- **Dataset**: `Popluation_census`
- **Table**: `global_population`
- **Fields**: Country-level population data including total, male, and female populations, male-to-female ratios, and more

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| `No API key was provided` | Ensure `.env` is loaded or env vars are set. Run `gcloud auth application-default login` |
| `quota exceeded` | Set a quota project: `gcloud auth application-default set-quota-project gcai-sep-26` |
| Cloud Run build fails | Ensure you run `gcloud run deploy` from **inside** the `population_census/` directory |
| Unauthorized user message | Change User ID in the sidebar to `pankaj` or `user` |
| Slow first response | The first query initializes the BigQuery toolset; subsequent queries are faster |
