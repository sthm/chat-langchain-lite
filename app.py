"""Chat LangChain Lite — simple chat UI."""

import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv(override=True)

def _logo_b64() -> str:
    path = Path(__file__).parent / "langchain-color.png"
    return base64.b64encode(path.read_bytes()).decode()

st.set_page_config(
    page_title="Chat LangChain Lite",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  * { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

  [data-testid="stAppViewContainer"] { background: #000000 !important; }
  [data-testid="stMainBlockContainer"] { background: #000000 !important; padding-top: 0 !important; }
  .block-container { padding-top: 0 !important; padding-bottom: 140px !important; max-width: 700px !important; }

  #MainMenu, footer, header,
  [data-testid="stDecoration"],
  [data-testid="stSidebar"],
  .stDeployButton { display: none !important; }

  /* header */
  .pg-header {
    display: flex;
    align-items: center;
    padding: 20px 0 18px;
    border-bottom: 1px solid #1c1c1c;
    margin-bottom: 32px;
  }
  .pg-brand-name { font-size: 15px; font-weight: 600; color: #ffffff; letter-spacing: -0.1px; }

  /* custom message bubbles */
  .pg-msg { display: flex; gap: 12px; margin-bottom: 16px; align-items: flex-start; }
  .pg-avatar {
    width: 32px; height: 32px; border-radius: 6px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 600; letter-spacing: -0.3px;
  }
  .pg-avatar-user { background: #27272a; color: #a1a1aa; }
  .pg-avatar-bot  { background: #172554; color: #93c5fd; }
  .pg-bubble {
    background: #0f0f0f;
    border: 1px solid #1c1c1c;
    border-radius: 10px;
    padding: 12px 16px;
    flex: 1;
  }
  .pg-bubble p, .pg-bubble li, .pg-bubble span, .pg-bubble div {
    color: #e4e4e7 !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
    margin: 0 0 4px 0 !important;
  }
  .pg-bubble strong { color: #ffffff !important; }
  .pg-bubble ul { padding-left: 18px !important; margin: 6px 0 !important; }
  .pg-bubble li { margin-bottom: 2px !important; }
  .pg-bubble pre {
    background: #050505 !important;
    border: 1px solid #1c1c1c !important;
    border-radius: 6px !important;
    padding: 10px 12px !important;
    overflow-x: auto !important;
  }
  .pg-bubble code {
    background: #050505 !important;
    color: #93c5fd !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-size: 13px !important;
    font-family: 'JetBrains Mono', ui-monospace, monospace !important;
  }
  .pg-bubble pre code { padding: 0 !important; background: transparent !important; }

  /* entire bottom bar — white/light grey */
  [data-testid="stChatInputContainer"],
  [data-testid="stChatInputContainer"]:focus-within,
  [data-testid="stChatInputContainer"]:focus,
  [data-testid="stChatInputContainer"]:active {
    background: #f4f4f5 !important;
    border: none !important;
    border-top: 1px solid #e4e4e7 !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 12px 16px !important;
  }
  [data-testid="stChatInputContainer"] > div,
  [data-testid="stChatInputContainer"] > div:focus-within {
    background: #f4f4f5 !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
  }
  [data-testid="stChatInput"],
  [data-testid="stChatInput"]:focus,
  [data-testid="stChatInput"]:focus-within {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
  }
  [data-testid="stChatInput"] textarea,
  [data-testid="stChatInput"] textarea:focus,
  [data-testid="stChatInput"] textarea:active,
  [data-testid="stChatInput"] textarea:hover,
  [data-testid="stChatInput"] textarea:focus-visible {
    background: #ffffff !important;
    border: 1px solid #e4e4e7 !important;
    border-radius: 10px !important;
    color: #09090b !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
    padding: 10px 14px !important;
    min-height: 44px !important;
    caret-color: #09090b !important;
    box-shadow: none !important;
    outline: none !important;
    -webkit-box-shadow: none !important;
  }
  [data-testid="stChatInput"] textarea::placeholder { color: #a1a1aa !important; }

  /* prebuilt question cards */
  .stButton button {
    background: linear-gradient(180deg, #0d0d10 0%, #0a0a0c 100%) !important;
    border: 1px solid #1f1f24 !important;
    color: #d4d4d8 !important;
    border-radius: 12px !important;
    font-size: 13px !important;
    line-height: 1.45 !important;
    padding: 14px 16px !important;
    width: 100% !important;
    min-height: 76px !important;
    text-align: left !important;
    white-space: normal !important;
    transition: border-color 0.15s, transform 0.15s, background 0.15s !important;
    font-weight: 500 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.4) !important;
  }
  .stButton button:hover {
    border-color: #3b82f6 !important;
    background: linear-gradient(180deg, #111319 0%, #0d0e12 100%) !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
  }
  .stButton button:active { transform: translateY(0) !important; }
  .pg-card-eyebrow {
    display: block;
    font-size: 10px !important;
    font-weight: 600 !important;
    color: #6b7280 !important;
    letter-spacing: 0.6px !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
  }
  .pg-suggestions-label {
    font-size: 11px;
    font-weight: 600;
    color: #52525b;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    text-align: center;
    margin: 8px 0 14px;
  }

  .stSpinner > div { border-top-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="pg-header">
  <div style="display:flex; align-items:center; gap:9px;">
    <img src="data:image/png;base64,{_logo_b64()}" width="26" height="26" style="display:block;"/>
    <span class="pg-brand-name">Chat LangChain Lite</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────
import uuid
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# ── Empty state ───────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown(f"""
    <div style="text-align:center; padding: 56px 0 36px;">
      <img src="data:image/png;base64,{_logo_b64()}" width="64" height="64" style="display:inline-block; opacity:0.95;"/>
      <div style="font-size:22px; font-weight:700; color:#ffffff; margin-top:18px; letter-spacing:-0.3px;">Chat LangChain Lite</div>
      <div style="font-size:13px; color:#52525b; margin-top:6px;">Ask anything about LangChain, LangGraph, LangSmith, and Deep Agents</div>
    </div>
    """, unsafe_allow_html=True)

    # Prebuilt cards. 2x3 grid, ordered to match the talk track:
    #   Row 1 (Phase 1 / truncation - "first fix"):
    #     - LangGraph walkthrough          - Production LangSmith setup
    #   Row 2 (Phase 3 / bad prompt - "regression prevention"):
    #     - What is LangSmith              - Django debugging (off-topic)
    #   Row 3 (Bonus - "iterative discovery"):
    #     - Official LangChain docs        - LangGraph min Python
    suggestions = [
        "Walk me through building a LangGraph agent end-to-end with middleware, persistence, streaming, HITL, and evals.",
        "Show me how to set up LangSmith tracing, datasets, offline evals, and online evaluators end-to-end.",
        "What is LangSmith and what is it used for?",
        "Help me debug my Django view function — it's throwing a 500.",
        "Where can I find the official LangChain documentation?",
        "What's the minimum Python version for LangGraph?",
    ]
    st.markdown('<div class="pg-suggestions-label">Try one of these</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, text in enumerate(suggestions):
        if cols[i % 2].button(text, key=f"sug_{i}"):
            st.session_state.pending = text
            st.rerun()

# ── Render messages as custom HTML ────────────────────────────────────────
import markdown as md_lib

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="pg-msg">
          <div class="pg-avatar pg-avatar-user">You</div>
          <div class="pg-bubble"><p>{msg["content"]}</p></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        body = md_lib.markdown(msg["content"], extensions=["fenced_code"])
        st.markdown(f"""
        <div class="pg-msg">
          <div class="pg-avatar pg-avatar-bot">LC</div>
          <div class="pg-bubble">{body}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Message Chat LangChain Lite...")

if "pending" in st.session_state:
    user_input = st.session_state.pop("pending")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Show user bubble immediately
    st.markdown(f"""
    <div class="pg-msg">
      <div class="pg-avatar pg-avatar-user">You</div>
      <div class="pg-bubble"><p>{user_input}</p></div>
    </div>
    """, unsafe_allow_html=True)

    # Stream assistant response into a placeholder
    st.markdown("""
    <div class="pg-msg" id="streaming-msg">
      <div class="pg-avatar pg-avatar-bot">LC</div>
      <div class="pg-bubble" id="streaming-bubble">
    """, unsafe_allow_html=True)

    placeholder = st.empty()
    response = ""

    try:
        from agent.agent import stream_agent
        for chunk in stream_agent(question=user_input, thread_id=st.session_state.thread_id):
            response += chunk
            placeholder.markdown(
                f'<div style="color:#e4e4e7;font-size:14px;line-height:1.7;">{response}</div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        response = f"Error: {e}"
        placeholder.markdown(response)

    st.markdown("</div></div>", unsafe_allow_html=True)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
