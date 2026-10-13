import os
import sys
import uuid

# Load environment before any google imports
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

import streamlit as st
from google.adk.runners import InMemoryRunner
from google.genai import types

# ── Import the agent app ─────────────────────────────────────────────────────
# Add parent directory so the package import works
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from population_census.agent import app  # noqa: E402


# ── Sample questions ──────────────────────────────────────────────────────────
SAMPLE_QUESTIONS = [
    "What is the total world population?",
    "Show top 10 most populated countries",
    "What is the population of India?",
    "Compare population of USA and China",
    "Which countries have population over 100 million?",
    "Show population growth rate by continent",
    "What are the least populated countries?",
    "Show population density of top 5 countries",
]


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Population Census Chatbot",
    page_icon="🌍",
    layout="centered",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Header styling */
    .main-header {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-header h1 {
        background: linear-gradient(135deg, #4ade80, #22d3ee, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 0.9rem;
    }

    /* Chat messages */
    .stChatMessage {
        border-radius: 12px !important;
        margin-bottom: 0.5rem !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] .stButton > button {
        text-align: left !important;
        font-size: 0.82rem !important;
        padding: 0.5rem 0.75rem !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        border-color: #4ade80 !important;
        background: rgba(74, 222, 128, 0.08) !important;
    }

    /* Token usage badge */
    .token-badge {
        display: inline-block;
        background: rgba(74,222,128,0.1);
        border: 1px solid rgba(74,222,128,0.25);
        color: #4ade80;
        font-size: 0.72rem;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        margin-top: 0.3rem;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Cached runner ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_runner():
    """Create and cache the InMemoryRunner (expensive, do once)."""
    return InMemoryRunner(app=app)


# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "user_id" not in st.session_state:
    st.session_state.user_id = "pankaj"

# Make sure ADK session exists
if "adk_session_created" not in st.session_state:
    runner = get_runner()
    runner.session_service.create_session_sync(
        app_name=app.name,
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id,
    )
    st.session_state.adk_session_created = True


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌍 Population Census")
    st.caption("Powered by Google ADK · Gemini 3.5 Flash")
    st.divider()

    st.markdown("**Try a sample question**")
    st.caption("Click to send instantly")
    for q in SAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True, key=f"sq_{q[:20]}"):
            st.session_state.pending_question = q

    st.divider()

    # User ID selector (controls access via before_agent_callback)
    new_user = st.text_input("User ID", value=st.session_state.user_id)
    if new_user != st.session_state.user_id:
        st.session_state.user_id = new_user
        # Create a fresh ADK session for the new user
        st.session_state.session_id = str(uuid.uuid4())
        runner = get_runner()
        runner.session_service.create_session_sync(
            app_name=app.name,
            user_id=new_user,
            session_id=st.session_state.session_id,
        )
        st.session_state.messages = []
        st.rerun()

    if st.button("🗑️  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        runner = get_runner()
        runner.session_service.create_session_sync(
            app_name=app.name,
            user_id=st.session_state.user_id,
            session_id=st.session_state.session_id,
        )
        st.rerun()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="main-header">'
    "<h1>🌍 Population Census Chatbot</h1>"
    "<p>Ask questions about global population data</p>"
    "</div>",
    unsafe_allow_html=True,
)


# ── Helper: call the agent ────────────────────────────────────────────────────
def ask_agent(user_text: str) -> tuple[str, dict]:
    """Send a message to the ADK agent and return (response_text, token_info)."""
    runner = get_runner()
    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_text)],
    )

    response_text = ""
    token_info = {}

    for event in runner.run(
        user_id=st.session_state.user_id,
        session_id=st.session_state.session_id,
        new_message=message,
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    response_text += part.text

        # Collect token usage if available
        usage = getattr(event, "usage_metadata", None)
        if usage:
            token_info["total"] = token_info.get("total", 0) + (
                getattr(usage, "total_token_count", 0) or 0
            )
            token_info["prompt"] = token_info.get("prompt", 0) + (
                getattr(usage, "prompt_token_count", 0) or 0
            )
            token_info["candidate"] = token_info.get("candidate", 0) + (
                getattr(usage, "candidates_token_count", 0) or 0
            )

    return response_text.strip(), token_info


# ── Render chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"] == "user" else "🌍"):
        st.markdown(msg["content"])
        if msg.get("tokens"):
            t = msg["tokens"]
            st.markdown(
                f'<span class="token-badge">🔢 Tokens — '
                f'Total: {t.get("total",0)} · '
                f'Prompt: {t.get("prompt",0)} · '
                f'Output: {t.get("candidate",0)}</span>',
                unsafe_allow_html=True,
            )


# ── Handle user input ────────────────────────────────────────────────────────
user_input = st.chat_input("Ask a population question…")

# Merge sidebar click with chat input
if st.session_state.pending_question:
    user_input = st.session_state.pending_question
    st.session_state.pending_question = None

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_input)

    # Get agent response
    with st.chat_message("assistant", avatar="🌍"):
        with st.spinner("Querying population data…"):
            response, tokens = ask_agent(user_input)

        if not response:
            response = "⚠️ No response received from the agent. Please try again."

        st.markdown(response)

        if tokens:
            st.markdown(
                f'<span class="token-badge">🔢 Tokens — '
                f'Total: {tokens.get("total",0)} · '
                f'Prompt: {tokens.get("prompt",0)} · '
                f'Output: {tokens.get("candidate",0)}</span>',
                unsafe_allow_html=True,
            )

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "tokens": tokens}
    )
