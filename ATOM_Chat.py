"""
A.T.O.M. - Autonomous Task Orchestration Machine
Simplified Layout: No Sidebar, Popup Menu, Inline File Input
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 1. PAGE CONFIG (No Sidebar)
# ============================================================
st.set_page_config(
    page_title="A.T.O.M.",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# 2. IMPORTS
# ============================================================
from modules.cortex import (
    ATOMCortex, 
    GROQ_AVAILABLE, 
    CREW_AVAILABLE, 
    OLLAMA_AVAILABLE,
    read_file_content
)
from modules.style_manager import get_css, get_settings

# ============================================================
# 3. APPLY CSS
# ============================================================
current_settings = get_settings(st.session_state)
theme = current_settings.get("theme", "dark")
st.markdown(get_css(theme, current_settings), unsafe_allow_html=True)

# Hide sidebar completely + Custom styling
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }
    
    .grand-header {
        text-align: center;
        padding: 1rem 0 1.5rem 0;
    }
    
    .grand-title {
        font-family: 'Inter', sans-serif;
        font-size: 4rem;
        font-weight: 700;
        letter-spacing: 0.2em;
        background: linear-gradient(135deg, #C9A227 0%, #E8D48A 40%, #C9A227 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    
    .grand-subtitle {
        font-size: 0.85rem;
        color: #8B949E;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }
    
    .status-inline {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        margin: 0 4px;
    }
    
    .status-online {
        background: #3FB95020;
        color: #3FB950;
        border: 1px solid #3FB95040;
    }
    
    .status-offline {
        background: #F8514920;
        color: #F85149;
        border: 1px solid #F8514940;
    }
    
    /* Wider chat input area */
    .main .block-container {
        max-width: 1000px;
        padding: 1rem 2rem 5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 4. MENU POPUP (replaces sidebar)
# ============================================================
@st.dialog("⚛️ A.T.O.M. Menu")
def open_menu():
    # Status
    st.markdown("**System Status**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "Online" if OLLAMA_AVAILABLE else "Offline"
        st.markdown(f"Local: **{status}**")
    with col2:
        status = "Online" if GROQ_AVAILABLE else "Offline"
        st.markdown(f"Cloud: **{status}**")
    with col3:
        status = "Online" if CREW_AVAILABLE else "Offline"
        st.markdown(f"Crew: **{status}**")
    
    st.markdown("---")
    
    # Navigation
    st.markdown("**Navigation**")
    
    if st.button("💬 Chat", use_container_width=True):
        st.rerun()
    if st.button("📝 Notes", use_container_width=True):
        st.switch_page("pages/notes.py")
    if st.button("📊 Telemetry", use_container_width=True):
        st.switch_page("pages/telemetry.py")
    if st.button("⚙️ Settings", use_container_width=True):
        st.switch_page("pages/settings.py")
    if st.button("ℹ️ About", use_container_width=True):
        st.switch_page("pages/about.py")
    
    st.markdown("---")
    
    # Actions
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.context_files = []
        if "cortex" in st.session_state:
            del st.session_state.cortex
        st.rerun()


# ============================================================
# 5. CORTEX & SESSION STATE
# ============================================================
def get_cortex():
    if "cortex" not in st.session_state:
        try:
            st.session_state.cortex = ATOMCortex()
        except:
            st.session_state.cortex = None
    return st.session_state.cortex

if "messages" not in st.session_state:
    st.session_state.messages = []

if "context_files" not in st.session_state:
    st.session_state.context_files = []


# ============================================================
# 6. HEADER + MENU BUTTON
# ============================================================
col_menu, col_space = st.columns([1, 10])
with col_menu:
    if st.button("☰", help="Open Menu"):
        open_menu()

st.markdown("""
<div class="grand-header">
    <h1 class="grand-title">A.T.O.M.</h1>
    <p class="grand-subtitle">Autonomous Task Orchestration Machine · v4.0 Cortex</p>
</div>
""", unsafe_allow_html=True)

# Status pills
status_html = ""
if OLLAMA_AVAILABLE:
    status_html += '<span class="status-inline status-online">Local AI</span>'
else:
    status_html += '<span class="status-inline status-offline">Local AI</span>'

if GROQ_AVAILABLE:
    status_html += '<span class="status-inline status-online">Cloud AI</span>'
else:
    status_html += '<span class="status-inline status-offline">Cloud AI</span>'

st.markdown(f'<div style="text-align: center; margin-bottom: 1rem;">{status_html}</div>', unsafe_allow_html=True)


# ============================================================
# 7. CHAT MESSAGES
# ============================================================
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "⚛️"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("thinking"):
            with st.expander("🧠 View Reasoning", expanded=False):
                for step in msg["thinking"]:
                    st.markdown(f"**{step['step']}** — {step['detail']}")
        st.markdown(msg["content"])


# ============================================================
# 8. INPUT AREA: FILE + CHAT (Side by Side)
# ============================================================
st.markdown("---")

# Show active files
if st.session_state.context_files:
    file_names = ", ".join([f["name"] for f in st.session_state.context_files])
    col1, col2 = st.columns([6, 1])
    with col1:
        st.info(f"� Attached: {file_names}")
    with col2:
        if st.button("Clear"):
            st.session_state.context_files = []
            st.rerun()

# Input row: File uploader (small) + Chat input (wide)
col_file, col_chat = st.columns([1, 5])

with col_file:
    uploaded = st.file_uploader(
        "📎",
        type=["txt", "md", "py", "json", "csv", "pdf"],
        label_visibility="collapsed",
        key="file_input"
    )
    
    if uploaded:
        content = read_file_content(uploaded)
        existing = [f["name"] for f in st.session_state.context_files]
        if uploaded.name not in existing:
            st.session_state.context_files.append({
                "name": uploaded.name,
                "content": content
            })
            st.rerun()

with col_chat:
    prompt = st.chat_input("Ask A.T.O.M. anything...")

# Process chat
if prompt:
    # Build context
    context_parts = []
    for f in st.session_state.context_files:
        context_parts.append(f"[FILE: {f['name']}]\n{f['content']}\n[END FILE]")
    
    full_prompt = "\n\n".join(context_parts) + "\n\nQuery: " + prompt if context_parts else prompt
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt, "thinking": None})
    
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant", avatar="⚛️"):
        with st.spinner("Processing..."):
            try:
                cortex = get_cortex()
                if cortex is None:
                    raise Exception("Cortex unavailable")
                
                response, thinking = cortex.process(full_prompt)
                
                if thinking:
                    with st.expander("🧠 View Reasoning", expanded=False):
                        for step in thinking:
                            st.markdown(f"**{step['step']}** — {step['detail']}")
                
                st.markdown(response)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "thinking": thinking
                })
            except Exception as e:
                error = f"Error: {e}"
                st.markdown(error)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error,
                    "thinking": None
                })
