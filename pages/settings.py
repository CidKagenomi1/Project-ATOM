"""
ATOM Settings Page
User Interface Customization - Full Featured
"""

import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.settings.style_manager import get_css, get_settings, THEMES, FONTS, DEFAULT_SETTINGS

st.set_page_config(
    page_title="ATOM - Settings",
    page_icon="⚙️",
    layout="wide"
)

# Apply current theme
current_settings = get_settings(st.session_state)
theme = current_settings.get("theme", "dark")
st.markdown(get_css(theme, current_settings), unsafe_allow_html=True)

# Additional styling for settings page
st.markdown("""
<style>
    .settings-card {
        background: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .settings-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #8B949E;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚛️ A.T.O.M.")
    st.caption("Settings")
    
    st.markdown("---")
    
    st.page_link("ATOM_Chat.py", label="💬 Chat")
    st.page_link("pages/notes.py", label="📝 Notes")
    st.page_link("pages/telemetry.py", label="📊 Telemetry")
    st.page_link("pages/settings.py", label="⚙️ Settings")
    st.page_link("pages/about.py", label="ℹ️ About")


# --- HEADER ---
st.markdown("## ⚙️ Settings")
st.caption("Personalize your A.T.O.M. experience")

st.markdown("---")


# === SECTION 1: VISUAL THEME ===
st.markdown("### 🎨 Visual Theme")

current_theme = st.session_state.get("setting_theme", "dark")

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "🌙 Midnight Luxury" if current_theme == "dark" else "🌙 Midnight Luxury",
        use_container_width=True,
        type="primary" if current_theme == "dark" else "secondary"
    ):
        st.session_state["setting_theme"] = "dark"
        st.rerun()

with col2:
    if st.button(
        "☀️ Daylight Executive",
        use_container_width=True,
        type="primary" if current_theme == "light" else "secondary"
    ):
        st.session_state["setting_theme"] = "light"
        st.rerun()

st.caption(f"Current: {THEMES.get(current_theme, THEMES['dark'])['name']}")

st.markdown("---")


# === SECTION 2: TYPOGRAPHY ===
st.markdown("### 📝 Typography")

col1, col2 = st.columns(2)

with col1:
    # Font Family
    st.markdown("**Font Family**")
    current_font = st.session_state.get("setting_font_family", "Inter")
    font_names = {k: v["name"] for k, v in FONTS.items()}
    
    selected_font = st.selectbox(
        "Font",
        options=list(FONTS.keys()),
        index=list(FONTS.keys()).index(current_font) if current_font in FONTS else 0,
        format_func=lambda x: font_names.get(x, x),
        label_visibility="collapsed"
    )
    
    if selected_font != current_font:
        st.session_state["setting_font_family"] = selected_font
        st.rerun()

with col2:
    # Font Size
    st.markdown("**Reading Comfort**")
    current_size = st.session_state.get("setting_font_size", 15)
    font_size = st.slider(
        "Size",
        min_value=13,
        max_value=20,
        value=current_size,
        label_visibility="collapsed"
    )
    
    if font_size != current_size:
        st.session_state["setting_font_size"] = font_size
        st.rerun()

st.markdown("---")


# === SECTION 3: EFFECTS ===
st.markdown("### ✨ Effects")

current_glass = st.session_state.get("setting_glass_effect", True)
glass_effect = st.toggle(
    "Glass Effect (Frosted transparency)",
    value=current_glass
)

if glass_effect != current_glass:
    st.session_state["setting_glass_effect"] = glass_effect
    st.rerun()

st.markdown("---")


# === PREVIEW ===
st.markdown("### 👁️ Preview")

preview_theme = THEMES.get(theme, THEMES["dark"])
preview_font = FONTS.get(current_settings.get("font_family", "Inter"), FONTS["Inter"])
preview_size = current_settings.get("font_size", 15)

st.markdown(f"""
<div style="
    background: {preview_theme['bg_card']};
    border: 1px solid {preview_theme['border']};
    border-radius: 12px;
    padding: 1.5rem;
">
    <h3 style="margin: 0 0 0.75rem 0; font-family: {preview_font['stack']}; color: {preview_theme['text_primary']};">
        A.T.O.M. Preview
    </h3>
    <p style="margin: 0; font-family: {preview_font['stack']}; font-size: {preview_size}px; color: {preview_theme['text_secondary']}; line-height: 1.6;">
        This is how your text will appear with the current settings. 
        The <span style="color: {preview_theme['accent']}; font-weight: 500;">accent color</span> highlights important elements.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")


# === RESET ===
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔄 Reset All", use_container_width=True):
        for key, value in DEFAULT_SETTINGS.items():
            st.session_state[f"setting_{key}"] = value
        st.success("Settings reset to defaults!")
        st.rerun()
