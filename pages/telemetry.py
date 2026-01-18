import streamlit as st
import os
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="ATOM - Telemetry",
    page_icon="📊",
    layout="wide"
)

# --- CSS STYLING (Elegant Classic Theme - Normalized Fonts) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400&display=swap');
    
    .stApp {
        background-color: #0a0a0a;
        color: #e8e8e8;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    #MainMenu, footer {visibility: hidden;}
    header[data-testid="stHeader"] {background: transparent;}
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif;
        font-weight: 500;
        letter-spacing: 0.05em;
        color: #e8e8e8;
        border-bottom: 1px solid #1a1a1a;
        padding-bottom: 0.75rem;
    }
    
    /* Text elements - but NOT icons */
    .stMarkdown p, .stMarkdown span, .stTextInput label {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    .stCaption {
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #888888;
    }
    
    [data-testid="stMetric"] {
        background-color: #111111;
        border: 1px solid #1a1a1a;
        padding: 1.5rem;
        border-radius: 4px;
    }
    
    [data-testid="stMetric"] label {
        color: #888888 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #c9a962 !important;
        font-family: 'Playfair Display', serif !important;
        font-size: 2rem !important;
    }
    
    .stDataFrame {
        border: 1px solid #1a1a1a !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #1a1a1a;
    }
    
    .stButton > button {
        background-color: transparent !important;
        color: #888888 !important;
        border: 1px solid #1a1a1a !important;
        border-radius: 4px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #c9a962 !important;
        color: #0a0a0a !important;
        border-color: #c9a962 !important;
    }
</style>
""", unsafe_allow_html=True)


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
