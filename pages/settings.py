"""
ATOM Settings Page
User Interface Customization
"""

import streamlit as st
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.style_manager import (
    generate_css, get_settings, DEFAULT_SETTINGS, THEMES, FONTS
)

st.set_page_config(
    page_title="ATOM - Settings",
    page_icon="⚙️",
    layout="wide"
)

# Apply current theme
settings = get_settings(st.session_state)
st.markdown(generate_css(settings), unsafe_allow_html=True)

# --- HEADER ---
st.markdown("## ⚙️ Settings")
st.caption("Customize your A.T.O.M. experience")

st.markdown("---")

# --- THEME SETTINGS ---
st.markdown("### 🎨 Appearance")

col1, col2 = st.columns(2)

with col1:
    # Theme selector
    current_theme = st.session_state.get("setting_theme", "dark")
    theme_options = {"Elegant Dark": "dark", "Clean Light": "light"}
    theme_labels = list(theme_options.keys())
    current_theme_label = "Elegant Dark" if current_theme == "dark" else "Clean Light"
    
    selected_theme_label = st.selectbox(
        "Theme",
        theme_labels,
        index=theme_labels.index(current_theme_label),
        help="Choose between dark and light mode"
    )
    st.session_state["setting_theme"] = theme_options[selected_theme_label]

with col2:
    # Font family
    current_font = st.session_state.get("setting_font_family", "Inter")
    font_options = list(FONTS.keys())
    
    selected_font = st.selectbox(
        "Font Family",
        font_options,
        index=font_options.index(current_font) if current_font in font_options else 0,
        help="Choose your preferred font"
    )
    st.session_state["setting_font_family"] = selected_font

# Font size slider
current_size = st.session_state.get("setting_font_size", 16)
font_size = st.slider(
    "Font Size",
    min_value=12,
    max_value=24,
    value=current_size,
    step=1,
    help="Adjust the base font size (in pixels)"
)
st.session_state["setting_font_size"] = font_size

st.markdown("---")

# --- DISPLAY SETTINGS ---
st.markdown("### 🖥️ Display Options")

col1, col2 = st.columns(2)

with col1:
    # Show decorations toggle
    current_decorations = st.session_state.get("setting_show_decorations", True)
    show_decorations = st.toggle(
        "Show Decorative Elements",
        value=current_decorations,
        help="Toggle bubble animations and decorative elements"
    )
    st.session_state["setting_show_decorations"] = show_decorations

with col2:
    # Accent color
    accent_colors = {
        "Gold": "#c9a962",
        "Purple": "#9333EA",
        "Blue": "#3B82F6",
        "Teal": "#14B8A6",
        "Rose": "#F43F5E"
    }
    current_accent = st.session_state.get("setting_accent_color", "#c9a962")
    accent_names = list(accent_colors.keys())
    
    # Find current accent name
    current_accent_name = "Gold"
    for name, color in accent_colors.items():
        if color == current_accent:
            current_accent_name = name
            break
    
    selected_accent = st.selectbox(
        "Accent Color",
        accent_names,
        index=accent_names.index(current_accent_name),
        help="Choose the accent color for highlights"
    )
    st.session_state["setting_accent_color"] = accent_colors[selected_accent]

st.markdown("---")

# --- PREVIEW ---
st.markdown("### 👁️ Preview")

preview_theme = THEMES.get(st.session_state.get("setting_theme", "dark"), THEMES["dark"])

st.markdown(f"""
<div style="
    background: {preview_theme['bg_secondary']};
    border: 1px solid {preview_theme['border']};
    border-radius: 12px;
    padding: 24px;
    margin: 16px 0;
">
    <h3 style="
        color: {preview_theme['text_primary']};
        font-family: 'Playfair Display', serif;
        margin: 0 0 12px 0;
        border: none;
    ">A.T.O.M. Preview</h3>
    <p style="
        color: {preview_theme['text_secondary']};
        font-family: {FONTS.get(selected_font, FONTS['Inter'])};
        font-size: {font_size}px;
        margin: 0;
    ">
        This is how your text will look with the current settings.
        The accent color is <span style="color: {accent_colors[selected_accent]}; font-weight: 600;">highlighted like this</span>.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- RESET ---
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔄 Reset to Defaults", use_container_width=True):
        for key, value in DEFAULT_SETTINGS.items():
            st.session_state[f"setting_{key}"] = value
        st.success("Settings reset!")
        st.rerun()

with col2:
    if st.button("✅ Apply & Reload", type="primary", use_container_width=True):
        st.success("Settings saved!")
        st.rerun()

st.markdown("---")

# --- NAVIGATION ---
with st.sidebar:
    st.markdown("### Navigation")
    st.page_link("ATOM_Chat.py", label="💬 Chat")
    st.page_link("pages/notes.py", label="📝 Notes")
    st.page_link("pages/telemetry.py", label="📊 Telemetry")
    st.page_link("pages/settings.py", label="⚙️ Settings")
    
    st.markdown("---")
    st.caption("Changes apply immediately across all pages.")
