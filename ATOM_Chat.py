"""
A.T.O.M. Chat Interface
Autonomous Task Orchestration Machine
With Dynamic CSS & Visual Cortex Status
"""

import streamlit as st
import os
import time
from dotenv import load_dotenv

# Import ATOMCortex from modules
from modules.cortex import ATOMCortex, GROQ_AVAILABLE, CREW_AVAILABLE, OLLAMA_AVAILABLE
from modules.style_manager import generate_css, get_settings, get_status_html

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ATOM - Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto"
)

load_dotenv()

# --- DYNAMIC CSS (from settings) ---
settings = get_settings(st.session_state)
st.markdown(generate_css(settings), unsafe_allow_html=True)


# --- CORTEX INITIALIZATION ---
def get_cortex():
    if "cortex_instance" not in st.session_state:
        try:
            st.session_state.cortex_instance = ATOMCortex()
        except Exception as e:
            st.session_state.cortex_instance = None
            st.error(f"Cortex init error: {e}")
    return st.session_state.cortex_instance


# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Sistem online, Sir. Siap melayani.", "thinking": None}
    ]


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### CORTEX STATUS")
    
    cortex = get_cortex()
    
    # Visual Dashboard Grid
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Local Model Status
        local_latency = "~2-5s" if OLLAMA_AVAILABLE else "—"
        st.markdown(
            get_status_html("LOCAL", OLLAMA_AVAILABLE, local_latency),
            unsafe_allow_html=True
        )
    
    with col2:
        # Groq Cloud Status
        groq_latency = "~0.5-2s" if GROQ_AVAILABLE else "—"
        st.markdown(
            get_status_html("GROQ", GROQ_AVAILABLE, groq_latency),
            unsafe_allow_html=True
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        # CrewAI Status
        st.markdown(
            get_status_html("CREW", CREW_AVAILABLE, "Multi-Agent"),
            unsafe_allow_html=True
        )
    
    with col4:
        # Overall System Status
        system_ok = cortex is not None
        st.markdown(
            get_status_html("SYSTEM", system_ok, "v4.0"),
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ACTIONS")
    
    if st.button("🔄 Reinitialize Cortex", use_container_width=True):
        if "cortex_instance" in st.session_state:
            del st.session_state.cortex_instance
        st.rerun()
    
    if st.button("🧹 Clear Memory", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": "Memory cleared. Ready.", "thinking": None}
        ]
        if "cortex_instance" in st.session_state:
            del st.session_state.cortex_instance
        st.rerun()
    
    # Save chat to Notes
    if st.button("💾 Save to Notes", use_container_width=True):
        if len(st.session_state.messages) > 1:
            try:
                from modules.note_brain import summarize_conversation
                from modules.note_storage import save_note
                from datetime import datetime
                
                with st.spinner("AI sedang merangkum..."):
                    summary = summarize_conversation(st.session_state.messages)
                
                save_note({
                    "title": f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "content": summary,
                    "type": "chat_log",
                    "tags": ["chat", "auto-saved"]
                })
                st.success("Tersimpan ke Smart Notes!")
            except Exception as e:
                st.error(f"Gagal: {e}")
        else:
            st.warning("Belum ada chat")
    
    st.markdown("---")
    
    # Navigation
    st.markdown("### NAVIGATION")
    st.page_link("ATOM_Chat.py", label="💬 Chat")
    st.page_link("pages/notes.py", label="📝 Notes")
    st.page_link("pages/telemetry.py", label="📊 Telemetry")
    st.page_link("pages/settings.py", label="⚙️ Settings")


# --- MAIN CONTENT ---
st.markdown("## A.T.O.M")
st.caption("AUTONOMOUS TASK ORCHESTRATION MACHINE · v4.0 CORTEX")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        # Show thinking process if available
        if msg.get("thinking"):
            with st.expander("🧠 Thinking Process", expanded=False):
                for step in msg["thinking"]:
                    st.markdown(f"**{step['step']}**")
                    st.caption(step['detail'])
                    st.markdown("---")
        
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Enter command..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt, "thinking": None})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        message_placeholder = st.empty()
        
        with st.spinner("Processing..."):
            try:
                cortex = get_cortex()
                if cortex is None:
                    raise Exception("Cortex tidak tersedia.")
                
                response, thinking_steps = cortex.process(prompt)
                
                # Show thinking process
                with thinking_placeholder.expander("🧠 Thinking Process", expanded=False):
                    for step in thinking_steps:
                        st.markdown(f"**{step['step']}**")
                        st.caption(step['detail'])
                        st.markdown("---")
                
                message_placeholder.markdown(response)
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response, 
                    "thinking": thinking_steps
                })
                
            except Exception as e:
                error_msg = f"Maaf Sir, ada error: {str(e)}"
                message_placeholder.markdown(error_msg)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": error_msg, 
                    "thinking": None
                })
