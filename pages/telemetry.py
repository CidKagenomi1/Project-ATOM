import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="ATOM - Telemetry",
    page_icon="T",
    layout="wide"
)

# --- DYNAMIC CSS ---
from modules.style_manager import get_css, get_settings

current_settings = get_settings(st.session_state)
theme = current_settings.get("theme", "dark")
st.markdown(get_css(theme, current_settings), unsafe_allow_html=True)


def load_telemetry():
    """Load telemetry data."""
    try:
        if os.path.exists("atom_telemetry.csv"):
            df = pd.read_csv("atom_telemetry.csv")
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
    except Exception as e:
        st.error(f"Error loading telemetry: {e}")
    return pd.DataFrame()


# --- HEADER ---
st.markdown("## 📊 TELEMETRY")
st.caption("SYSTEM MONITORING · ATOM v3.1")

# Load Data
df = load_telemetry()

if df.empty:
    st.warning("No telemetry data available yet. Start chatting with ATOM to generate data.")
else:
    # --- METRICS ROW ---
    st.markdown("### OVERVIEW")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("TOTAL QUERIES", len(df))
    
    with col2:
        avg_time = df["response_time"].mean()
        st.metric("AVG RESPONSE", f"{avg_time:.2f}s")
    
    with col3:
        success_rate = (df["status"] == "SUCCESS").sum() / len(df) * 100
        st.metric("SUCCESS RATE", f"{success_rate:.0f}%")
    
    with col4:
        # Most used model
        top_model = df["model_used"].value_counts().idxmax() if len(df) > 0 else "N/A"
        st.metric("TOP MODEL", top_model)
    
    st.markdown("---")
    
    # --- MODEL BREAKDOWN ---
    st.markdown("### MODEL USAGE")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        model_counts = df["model_used"].value_counts()
        for model, count in model_counts.items():
            pct = (count / len(df)) * 100
            if "Gemini" in model:
                color = "🟢"
            elif "Llama" in model:
                color = "🟡"
            elif "Crew" in model:
                color = "🔵"
            else:
                color = "🔴"
            st.markdown(f"{color} **{model}**: {count} queries ({pct:.1f}%)")
    
    with col2:
        # Simple bar chart
        st.bar_chart(model_counts)
    
    st.markdown("---")
    
    # --- RESPONSE TIME ANALYSIS ---
    st.markdown("### RESPONSE TIME")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("FASTEST", f"{df['response_time'].min():.2f}s")
    with col2:
        st.metric("SLOWEST", f"{df['response_time'].max():.2f}s")
    with col3:
        st.metric("MEDIAN", f"{df['response_time'].median():.2f}s")
    
    # Response time by model
    st.caption("Average response time per model:")
    avg_by_model = df.groupby("model_used")["response_time"].mean().sort_values()
    st.bar_chart(avg_by_model)
    
    st.markdown("---")
    
    # --- RECENT ACTIVITY ---
    st.markdown("### ACTIVITY LOG")
    
    # Show last 20 entries
    recent = df.tail(20).iloc[::-1].copy()
    recent["timestamp"] = recent["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    recent = recent[["timestamp", "model_used", "response_time", "user_input"]]
    recent.columns = ["Time", "Model", "Duration (s)", "Query"]
    
    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### NAVIGATION")
    st.page_link("ATOM_Chat.py", label="💬 Chat", icon="💬")
    st.page_link("pages/telemetry.py", label="📊 Telemetry", icon="📊")
    
    st.markdown("---")
    
    if st.button("REFRESH DATA"):
        st.rerun()
