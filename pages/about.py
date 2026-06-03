"""
ATOM - About Page
System Architecture and Capabilities
"""

import streamlit as st
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.style_manager import get_css, get_settings

st.set_page_config(
    page_title="ATOM - About",
    page_icon="i",
    layout="wide"
)

# Apply theme
current_settings = get_settings(st.session_state)
theme = current_settings.get("theme", "dark")
st.markdown(get_css(theme, current_settings), unsafe_allow_html=True)


# --- HEADER ---
st.markdown("# About A.T.O.M.")
st.markdown("**Autonomous Task Orchestration Machine** | Version 3.5 Cortex")

st.markdown("---")


# --- ARCHITECTURE ---
st.markdown("## System Architecture")

st.markdown("""
A.T.O.M. implements a **Hybrid AI Architecture** designed for reliability and performance.
The system prioritizes local processing while maintaining cloud fallback capabilities.
""")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Primary: Local Processing")
    st.markdown("""
    - **Model**: Llama 3.2 via Ollama
    - **Latency**: 2-5 seconds
    - **Privacy**: Data stays on device
    - **Timeout**: 40 second kill switch
    """)

with col2:
    st.markdown("### Fallback: Cloud AI")
    st.markdown("""
    - **Primary Cloud**: Groq (Llama 3.3 70B)
    - **Secondary Cloud**: Google Gemini 1.5 Flash
    - **Latency**: 0.5-2 seconds
    - **Activation**: On local timeout or failure
    """)

st.markdown("---")


# --- ROUTING LOGIC ---
st.markdown("## Request Routing")

st.markdown("""
The Neural Router analyzes each input and determines the optimal processing path:

| Route | Trigger | Handler |
|-------|---------|---------|
| ACTION | System commands, file operations | ATOM Interpreter |
| CREW | Deep research requests | CrewAI Multi-Agent |
| AI | General queries | Timeout Failover Chain |

The Timeout Failover Chain ensures response delivery:

```
User Input → Ollama (40s timeout) → Groq Cloud → Gemini → Error Response
```
""")

st.markdown("---")


# --- CAPABILITIES ---
st.markdown("## Capabilities")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Analysis")
    st.markdown("""
    - Code review and debugging
    - Data interpretation
    - Document summarization
    - Research synthesis
    """)

with col2:
    st.markdown("### Generation")
    st.markdown("""
    - Code generation
    - Technical writing
    - Content creation
    - Format conversion
    """)

with col3:
    st.markdown("### Automation")
    st.markdown("""
    - System commands
    - File operations
    - Web scraping
    - Task orchestration
    """)

st.markdown("---")


# --- MODULES ---
st.markdown("## System Modules")

st.markdown("""
| Module | File | Purpose |
|--------|------|---------|
| Cortex | `modules/cortex.py` | Core AI routing and failover logic |
| Sentinel | `modules/cortex.py` | Telemetry and logging system |
| Librarian | `modules/cortex.py` | Conversation memory management |
| Note Brain | `modules/note_brain.py` | Smart Notes AI functions |
| Note Storage | `modules/note_storage.py` | Notes CRUD operations |
| CrewAI | `crew_atom.py` | Multi-agent research system |
| Interpreter | `atom_interpreter.py` | System action execution |
""")

st.markdown("---")


# --- REQUIREMENTS ---
st.markdown("## Dependencies")

st.markdown("""
**Python**: 3.9+

**Core Dependencies**:
- `streamlit` - Web interface
- `langchain-groq` - Groq LLM integration
- `langchain-ollama` - Local LLM integration
- `langchain-google-genai` - Gemini integration
- `crewai` - Multi-agent framework

**Optional**:
- `beautifulsoup4` - Web scraping
- `PyPDF2` - PDF text extraction
""")

st.markdown("---")


# --- FOOTER ---
st.markdown("## Configuration")

st.markdown("""
**Environment Variables**:
```
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
```

**Local Model Setup**:
```bash
ollama serve
ollama pull llama3.2
```
""")

st.markdown("---")

st.caption("A.T.O.M. v3.5 Cortex | Built with Streamlit and LangChain")


# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### Navigation")
    st.page_link("ATOM_Chat.py", label="Chat")
    st.page_link("pages/notes.py", label="Notes")
    st.page_link("pages/telemetry.py", label="Telemetry")
    st.page_link("pages/settings.py", label="Settings")
    st.page_link("pages/about.py", label="About")
