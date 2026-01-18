"""
ATOM Style Manager
Centralized CSS generation based on user settings.
"""

# Default theme configuration
DEFAULT_SETTINGS = {
    "theme": "dark",  # "dark" or "light"
    "font_family": "Inter",
    "font_size": 16,
    "show_decorations": True,
    "accent_color": "#c9a962"
}

# Theme color palettes
THEMES = {
    "dark": {
        "bg_primary": "#0a0a0a",
        "bg_secondary": "#111111",
        "bg_tertiary": "#1a1a1a",
        "text_primary": "#e8e8e8",
        "text_secondary": "#888888",
        "border": "#222222",
        "accent": "#c9a962",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444"
    },
    "light": {
        "bg_primary": "#f8f9fa",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#e9ecef",
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "border": "#dee2e6",
        "accent": "#6366f1",
        "success": "#22c55e",
        "warning": "#eab308",
        "error": "#dc2626"
    }
}

# Available fonts
FONTS = {
    "Inter": "'Inter', 'Segoe UI', sans-serif",
    "Roboto": "'Roboto', sans-serif",
    "Courier New": "'Courier New', monospace",
    "Comic Sans": "'Comic Sans MS', cursive"
}


def get_settings(session_state):
    """Get current settings from session state or defaults."""
    settings = {}
    for key, default_value in DEFAULT_SETTINGS.items():
        settings[key] = session_state.get(f"setting_{key}", default_value)
    return settings


def generate_css(settings: dict) -> str:
    """Generate dynamic CSS based on user settings."""
    
    theme = THEMES.get(settings.get("theme", "dark"), THEMES["dark"])
    font_family = FONTS.get(settings.get("font_family", "Inter"), FONTS["Inter"])
    font_size = settings.get("font_size", 16)
    
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=Roboto:wght@300;400;500&display=swap');
        
        .stApp {{
            background-color: {theme['bg_primary']};
            color: {theme['text_primary']};
            font-family: {font_family};
            font-size: {font_size}px;
        }}
        
        #MainMenu, footer {{visibility: hidden;}}
        header[data-testid="stHeader"] {{background: transparent;}}
        
        .main .block-container {{
            padding: 2rem 3rem;
            max-width: 1000px;
        }}
        
        h1, h2, h3 {{
            font-family: 'Playfair Display', serif;
            font-weight: 500;
            letter-spacing: 0.05em;
            color: {theme['text_primary']};
            border-bottom: 1px solid {theme['border']};
            padding-bottom: 0.75rem;
        }}
        
        .stCaption {{
            font-family: {font_family};
            font-size: {font_size - 2}px;
            color: {theme['text_secondary']};
        }}
        
        [data-testid="stSidebar"] {{
            background-color: {theme['bg_primary']};
            border-right: 1px solid {theme['border']};
        }}
        
        .stChatInput > div {{
            background-color: {theme['bg_secondary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        .stChatInput input {{
            background-color: {theme['bg_secondary']} !important;
            color: {theme['text_primary']} !important;
            font-family: {font_family} !important;
            font-size: {font_size}px !important;
        }}
        
        .stChatMessage {{
            background-color: transparent !important;
            border-left: 3px solid {theme['border']} !important;
            border-radius: 0 !important;
            padding: 1.25rem 1.75rem !important;
        }}
        
        .stChatMessage[data-testid="stChatMessageAssistant"] {{
            border-left-color: {theme['accent']} !important;
        }}
        
        .stChatMessage p {{
            color: {theme['text_primary']} !important;
            font-family: {font_family} !important;
            font-size: {font_size}px !important;
            line-height: 1.7 !important;
        }}
        
        .stChatMessage .stAvatar {{ display: none !important; }}
        
        .stChatMessage code, .stChatMessage pre {{
            font-family: 'JetBrains Mono', 'Courier New', monospace !important;
            background-color: {theme['bg_secondary']} !important;
            border-radius: 4px !important;
        }}
        
        .stButton > button {{
            background-color: {theme['bg_secondary']} !important;
            color: {theme['text_secondary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 6px !important;
            font-family: {font_family} !important;
            font-size: {font_size - 2}px !important;
            transition: all 0.2s ease !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['accent']} !important;
            color: {theme['bg_primary']} !important;
            border-color: {theme['accent']} !important;
        }}
        
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {{
            background-color: {theme['bg_secondary']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 6px !important;
        }}
        
        .stSuccess {{
            background-color: {theme['bg_secondary']} !important;
            border-left: 3px solid {theme['success']} !important;
            color: {theme['success']} !important;
        }}
        
        .stWarning {{
            background-color: {theme['bg_secondary']} !important;
            border-left: 3px solid {theme['warning']} !important;
            color: {theme['warning']} !important;
        }}
        
        .stError {{
            background-color: {theme['bg_secondary']} !important;
            border-left: 3px solid {theme['error']} !important;
            color: {theme['error']} !important;
        }}
        
        .streamlit-expanderHeader {{
            background-color: {theme['bg_secondary']} !important;
            border: 1px solid {theme['border']} !important;
            color: {theme['text_secondary']} !important;
        }}
        
        .streamlit-expanderContent {{
            background-color: {theme['bg_tertiary']} !important;
            border: 1px solid {theme['border']} !important;
            border-top: none !important;
        }}
        
        /* Status indicators */
        .status-online {{
            color: {theme['success']};
            font-weight: 600;
        }}
        .status-offline {{
            color: {theme['error']};
            font-weight: 600;
        }}
        .status-card {{
            background: {theme['bg_secondary']};
            border: 1px solid {theme['border']};
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }}
    </style>
    """
    
    return css


def get_status_html(name: str, is_online: bool, latency: str = "—") -> str:
    """Generate HTML for a status indicator."""
    status_class = "status-online" if is_online else "status-offline"
    status_icon = "🟢" if is_online else "🔴"
    status_text = "ONLINE" if is_online else "OFFLINE"
    
    return f"""
    <div class="status-card">
        <div style="font-size: 11px; color: #888; margin-bottom: 4px;">{name}</div>
        <div class="{status_class}">{status_icon} {status_text}</div>
        <div style="font-size: 10px; color: #666; margin-top: 4px;">⚡ {latency}</div>
    </div>
    """
