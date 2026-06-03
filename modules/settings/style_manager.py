"""
ATOM Style Manager - Luxury Edition
"5-Star Digital Hotel" Design Language
Elegant • Clean • Premium • Ergonomic
"""

# Default settings
DEFAULT_SETTINGS = {
    "theme": "dark",
    "font_family": "Inter",
    "font_size": 16,
    "glass_effect": True
}

# Theme palettes
THEMES = {
    "dark": {
        "name": "Midnight Luxury",
        "bg_primary": "#0E1117",
        "bg_card": "#161B22",
        "bg_elevated": "#1C2128",
        "bg_input": "#21262D",
        "text_primary": "#F0F6FC",
        "text_secondary": "#8B949E",
        "text_muted": "#6E7681",
        "border": "#30363D",
        "border_subtle": "#21262D",
        "accent": "#C9B037",  # Subtle Gold
        "accent_hover": "#D4BC4A",
        "accent_blue": "#58A6FF",  # Platinum Blue
        "success": "#3FB950",
        "warning": "#D29922",
        "error": "#F85149"
    },
    "light": {
        "name": "Daylight Executive",
        "bg_primary": "#FFFFFF",
        "bg_card": "#F6F8FA",
        "bg_elevated": "#FFFFFF",
        "bg_input": "#F6F8FA",
        "text_primary": "#24292F",
        "text_secondary": "#57606A",
        "text_muted": "#8C959F",
        "border": "#D0D7DE",
        "border_subtle": "#E8EBEF",
        "accent": "#0969DA",  # Executive Blue
        "accent_hover": "#0550AE",
        "accent_blue": "#0969DA",
        "success": "#1A7F37",
        "warning": "#9A6700",
        "error": "#CF222E"
    }
}

# Font families
FONTS = {
    "Inter": {
        "name": "Modern Sans (Inter)",
        "stack": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    },
    "Playfair": {
        "name": "Elegant Serif (Playfair)",
        "stack": "'Playfair Display', Georgia, serif"
    },
    "Roboto": {
        "name": "Technical (Roboto)",
        "stack": "'Roboto', 'Helvetica Neue', Arial, sans-serif"
    }
}

FONT_MONO = "'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas, monospace"


def get_settings(session_state) -> dict:
    """Get current settings from session state."""
    settings = {}
    for key, default in DEFAULT_SETTINGS.items():
        settings[key] = session_state.get(f"setting_{key}", default)
    return settings


def get_theme_from_session(session_state) -> str:
    """Get current theme name."""
    return session_state.get("setting_theme", "dark")


def get_css(theme: str = "dark", settings: dict = None) -> str:
    """
    Generate luxury CSS for the specified theme.
    """
    if settings is None:
        settings = DEFAULT_SETTINGS
    
    t = THEMES.get(theme, THEMES["dark"])
    font_key = settings.get("font_family", "Inter")
    font_stack = FONTS.get(font_key, FONTS["Inter"])["stack"]
    font_size = settings.get("font_size", 16)
    glass = settings.get("glass_effect", True)
    
    # Glass effect values
    glass_bg = f"rgba(22, 27, 34, 0.85)" if theme == "dark" else f"rgba(255, 255, 255, 0.9)"
    glass_backdrop = "blur(12px)" if glass else "none"
    
    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Playfair+Display:wght@400;500;600&family=Roboto:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');
        
        /* === BASE === */
        .stApp {{
            background-color: {t['bg_primary']};
            color: {t['text_primary']};
            font-family: {font_stack};
            font-size: {font_size}px;
            line-height: 1.7;
        }}
        
        #MainMenu, footer {{visibility: hidden;}}
        
        header[data-testid="stHeader"] {{
            background: transparent !important;
        }}
        
        .main .block-container {{
            padding: 2rem 3rem 6rem 3rem;
            max-width: 900px;
        }}
        
        /* === TYPOGRAPHY === */
        h1, h2, h3, h4 {{
            font-family: {font_stack};
            font-weight: 600;
            color: {t['text_primary']};
            letter-spacing: -0.01em;
            margin-bottom: 0.75rem;
        }}
        
        h1 {{ font-size: 1.75rem; }}
        h2 {{ font-size: 1.4rem; }}
        h3 {{ font-size: 1.15rem; }}
        
        p, li, span {{
            color: {t['text_primary']};
        }}
        
        a {{
            color: {t['accent_blue']};
            text-decoration: none;
            transition: opacity 0.2s ease;
        }}
        
        a:hover {{
            opacity: 0.8;
        }}
        
        /* === CODE === */
        code {{
            font-family: {FONT_MONO};
            background: {t['bg_card']};
            color: {t['accent_blue']};
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.9em;
        }}
        
        pre {{
            font-family: {FONT_MONO};
            background: {t['bg_card']} !important;
            border: 1px solid {t['border_subtle']};
            border-radius: 12px;
            padding: 1.25rem;
            font-size: 0.85em;
            overflow-x: auto;
        }}
        
        /* === SIDEBAR === */
        [data-testid="stSidebar"] {{
            background-color: {t['bg_card']};
            border-right: 1px solid {t['border_subtle']};
        }}
        
        [data-testid="stSidebar"] > div:first-child {{
            padding: 2rem 1.5rem;
        }}
        
        /* === CARDS === */
        .luxury-card {{
            background: {glass_bg if glass else t['bg_card']};
            backdrop-filter: {glass_backdrop};
            -webkit-backdrop-filter: {glass_backdrop};
            border: 1px solid {t['border_subtle']};
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .luxury-card:hover {{
            border-color: {t['border']};
        }}
        
        .card-title {{
            font-size: 0.85rem;
            font-weight: 600;
            color: {t['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 1.25rem;
        }}
        
        /* === INPUTS === */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background-color: {t['bg_input']} !important;
            color: {t['text_primary']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 12px !important;
            padding: 0.875rem 1rem !important;
            font-family: {font_stack} !important;
            font-size: {font_size}px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {t['accent']} !important;
            box-shadow: 0 0 0 3px {t['accent']}20 !important;
        }}
        
        /* === SELECT === */
        .stSelectbox > div > div {{
            background-color: {t['bg_input']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 12px !important;
            transition: border-color 0.2s ease !important;
        }}
        
        .stSelectbox > div > div:hover {{
            border-color: {t['border']} !important;
        }}
        
        /* === SLIDER === */
        .stSlider > div > div > div {{
            background-color: {t['border_subtle']} !important;
        }}
        
        .stSlider > div > div > div > div {{
            background-color: {t['accent']} !important;
        }}
        
        /* === BUTTONS === */
        .stButton > button {{
            background-color: {t['bg_card']} !important;
            color: {t['text_primary']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 10px !important;
            font-family: {font_stack} !important;
            font-size: {font_size - 1}px !important;
            font-weight: 500 !important;
            padding: 0.625rem 1.25rem !important;
            transition: all 0.25s ease !important;
        }}
        
        .stButton > button:hover {{
            background-color: {t['bg_elevated']} !important;
            border-color: {t['accent']} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stButton > button[kind="primary"] {{
            background-color: {t['accent']} !important;
            border-color: {t['accent']} !important;
            color: #FFFFFF !important;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background-color: {t['accent_hover']} !important;
        }}
        
        /* === CHAT === */
        .stChatInput {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem 3rem 1.5rem;
            background: linear-gradient(transparent, {t['bg_primary']} 20%);
        }}
        
        .stChatInput > div {{
            max-width: 900px;
            margin: 0 auto;
            background-color: {t['bg_card']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 24px rgba(0,0,0,0.12);
        }}
        
        .stChatInput input {{
            background-color: transparent !important;
            color: {t['text_primary']} !important;
            font-family: {font_stack} !important;
            font-size: {font_size}px !important;
            padding: 1rem !important;
        }}
        
        .stChatMessage {{
            background-color: {t['bg_card']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 16px !important;
            padding: 1.25rem 1.5rem !important;
            margin-bottom: 1rem !important;
            transition: border-color 0.2s ease;
        }}
        
        .stChatMessage:hover {{
            border-color: {t['border']} !important;
        }}
        
        .stChatMessage p {{
            color: {t['text_primary']} !important;
            font-family: {font_stack} !important;
            font-size: {font_size}px !important;
            line-height: 1.7 !important;
        }}
        
        /* === EXPANDER === */
        .streamlit-expanderHeader {{
            background-color: {t['bg_card']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-radius: 12px !important;
            color: {t['text_secondary']} !important;
            font-family: {font_stack} !important;
            font-size: {font_size - 1}px !important;
            padding: 0.875rem 1rem !important;
            transition: all 0.2s ease !important;
        }}
        
        .streamlit-expanderHeader:hover {{
            border-color: {t['border']} !important;
            color: {t['text_primary']} !important;
        }}
        
        .streamlit-expanderContent {{
            background-color: {t['bg_primary']} !important;
            border: 1px solid {t['border_subtle']} !important;
            border-top: none !important;
            border-radius: 0 0 12px 12px !important;
            padding: 1.25rem !important;
        }}
        
        /* === TABS === */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {t['bg_card']};
            border-radius: 12px;
            padding: 6px;
            gap: 4px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            color: {t['text_secondary']};
            font-family: {font_stack};
            font-weight: 500;
            padding: 0.5rem 1rem;
            transition: all 0.2s ease;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {t['bg_primary']};
            color: {t['text_primary']};
        }}
        
        /* === FILE UPLOADER === */
        [data-testid="stFileUploader"] {{
            background-color: {t['bg_card']};
            border: 2px dashed {t['border_subtle']};
            border-radius: 12px;
            padding: 1.5rem;
            transition: border-color 0.2s ease;
        }}
        
        [data-testid="stFileUploader"]:hover {{
            border-color: {t['accent']};
        }}
        
        /* === ALERTS === */
        .stSuccess, .stInfo, .stWarning, .stError {{
            border-radius: 12px !important;
            border-left-width: 4px !important;
            padding: 1rem 1.25rem !important;
        }}
        
        .stSuccess {{ background-color: {t['bg_card']} !important; border-left-color: {t['success']} !important; }}
        .stInfo {{ background-color: {t['bg_card']} !important; border-left-color: {t['accent_blue']} !important; }}
        .stWarning {{ background-color: {t['bg_card']} !important; border-left-color: {t['warning']} !important; }}
        .stError {{ background-color: {t['bg_card']} !important; border-left-color: {t['error']} !important; }}
        
        /* === METRICS === */
        [data-testid="stMetric"] {{
            background-color: {t['bg_card']};
            border: 1px solid {t['border_subtle']};
            border-radius: 12px;
            padding: 1.25rem;
        }}
        
        [data-testid="stMetric"] label {{
            color: {t['text_secondary']} !important;
            font-size: 0.85rem !important;
        }}
        
        [data-testid="stMetric"] [data-testid="stMetricValue"] {{
            color: {t['accent']} !important;
            font-size: 1.75rem !important;
            font-weight: 600 !important;
        }}
        
        /* === STATUS BOX === */
        .status-box {{
            background: {t['bg_card']};
            border: 1px solid {t['border_subtle']};
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            font-size: 0.85rem;
        }}
        
        .status-online {{ color: {t['success']}; font-weight: 500; }}
        .status-offline {{ color: {t['error']}; font-weight: 500; }}
        
        /* === TOGGLE === */
        .stToggle label {{
            color: {t['text_primary']} !important;
        }}
    </style>
    """
    
    return css


def get_status_box(label: str, status: str, is_online: bool) -> str:
    """Generate HTML for a minimal status box."""
    status_class = "status-online" if is_online else "status-offline"
    return f'''
    <div class="status-box">
        <span style="opacity: 0.6;">{label}</span>
        <span class="{status_class}" style="float: right;">{status}</span>
    </div>
    '''


def render_card(title: str, content: str) -> str:
    """Render a luxury card with title."""
    return f'''
    <div class="luxury-card">
        <div class="card-title">{title}</div>
        {content}
    </div>
    '''
