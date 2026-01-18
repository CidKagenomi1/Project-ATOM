import streamlit as st
import os
from dotenv import load_dotenv

# Import ATOMCortex from modules
from modules.cortex import ATOMCortex, GROQ_AVAILABLE, CREW_AVAILABLE

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="ATOM - Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto"
)

load_dotenv()

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600&display=swap');
    
    .stApp {
        background-color: #000000;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 300;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #FFFFFF;
        border-bottom: 1px solid #333333;
        padding-bottom: 0.5rem;
    }
    
    .stCaption {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #666666;
    }
    
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #1A1A1A;
    }
    
    .stChatInput > div {
        background-color: #000000 !important;
        border: 1px solid #333333 !important;
        border-radius: 0 !important;
    }
    
    .stChatInput input {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .stChatMessage {
        background-color: transparent !important;
        border-left: 2px solid #333333 !important;
        border-radius: 0 !important;
        padding: 1rem 1.5rem !important;
    }
    
    .stChatMessage[data-testid="stChatMessageAssistant"] {
        border-left-color: #FFFFFF !important;
    }
    
    .stChatMessage p {
        color: #CCCCCC !important;
        font-family: 'Inter', sans-serif !important;
        line-height: 1.6 !important;
    }
    
    .stChatMessage .stAvatar { display: none !important; }
    
    .stButton > button {
        background-color: transparent !important;
        color: #888888 !important;
        border: 1px solid #333333 !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
    }
    
    .stButton > button:hover {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }
    
    .stSuccess, .stWarning, .stError {
        background-color: transparent !important;
        border-radius: 0 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.7rem !important;
    }
    
    .stSuccess { border-left: 2px solid #00FF00 !important; color: #00FF00 !important; }
    .stWarning { border-left: 2px solid #FFAA00 !important; color: #FFAA00 !important; }
    .stError { border-left: 2px solid #FF3333 !important; color: #FF3333 !important; }
    
    .streamlit-expanderHeader {
        background-color: #0A0A0A !important;
        border: 1px solid #222222 !important;
        color: #888888 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.75rem !important;
    }
    
    .streamlit-expanderContent {
        background-color: #050505 !important;
        border: 1px solid #222222 !important;
        border-top: none !important;
    }
</style>
""", unsafe_allow_html=True)


# --- CORTEX ---
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
    st.markdown("### CORTEX")
    st.markdown("---")
    
    cortex = get_cortex()
    if cortex:
        st.success("ONLINE")
        st.caption(f"Groq: {'Y' if GROQ_AVAILABLE else 'N'} | Crew: {'Y' if CREW_AVAILABLE else 'N'}")
    else:
        st.error("ERROR")
        if st.button("REINIT"):
            if "cortex_instance" in st.session_state:
                del st.session_state.cortex_instance
            st.rerun()
    
    st.markdown("---")
    st.markdown("### NAVIGATION")
    st.page_link("ATOM_Chat.py", label="💬 Chat")
    st.page_link("pages/telemetry.py", label="📊 Telemetry")
    st.page_link("pages/notes.py", label="📝 Notes")
    
    st.markdown("---")
    
    # Save chat to Smart Notes
    if st.button("💾 Save to Notes"):
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
    
    if st.button("CLEAR MEMORY"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Memory cleared. Ready.", "thinking": None}
        ]
        if "cortex_instance" in st.session_state:
            del st.session_state.cortex_instance
        st.rerun()


# --- MAIN ---
st.markdown("## A.T.O.M")
st.caption("AUTONOMOUS TASK ORCHESTRATION MACHINE · v3.2 CORTEX")

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("thinking"):
            with st.expander("🧠 Thinking Process", expanded=False):
                for step in msg["thinking"]:
                    st.markdown(f"**{step['step']}**")
                    st.caption(step['detail'])
                    st.markdown("---")
        
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Enter command..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "thinking": None})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thinking_placeholder = st.empty()
        message_placeholder = st.empty()
        
        with st.spinner("Processing..."):
            try:
                cortex = get_cortex()
                if cortex is None:
                    raise Exception("Cortex tidak tersedia.")
                
                response, thinking_steps = cortex.process(prompt)
                
                with thinking_placeholder.expander("🧠 Thinking Process", expanded=False):
                    for step in thinking_steps:
                        st.markdown(f"**{step['step']}**")
                        st.caption(step['detail'])
                        st.markdown("---")
                
                message_placeholder.markdown(response)
                
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
