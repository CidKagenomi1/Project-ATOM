"""
ATOM Smart Notes - UI with Floating Bubble Notes
Obsidian + NotebookLLM Style Knowledge Management
"""

import streamlit as st
import os
import sys
import json
import random
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.notes.note_storage import (
    get_all_notes, get_note, create_note, update_note, delete_note,
    search_notes, get_all_tags, get_note_preview, get_stats
)
from modules.notes.note_brain import (
    chat_with_context, auto_tag, summarize_conversation, generate_title, refine_text
)

# Try to import CrewAI
try:
    from modules.core.crew import run_research_crew
    CREW_AVAILABLE = True
except ImportError:
    CREW_AVAILABLE = False
    def run_research_crew(topic):
        return f"[CREW OFFLINE] CrewAI not available. Topic: {topic}"

st.set_page_config(
    page_title="ATOM - Smart Notes",
    page_icon="📚",
    layout="wide"
)

# --- DYNAMIC CSS (from settings) ---
from modules.settings.style_manager import get_css, get_settings

current_settings = get_settings(st.session_state)
theme = current_settings.get("theme", "dark")
st.markdown(get_css(theme, current_settings), unsafe_allow_html=True)

# Additional Notes-specific styles
st.markdown("""
<style>
    .tag {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 12px;
        margin: 2px;
        color: #c9a962;
    }
    
    .chat-user { 
        background: #111; 
        border-left: 3px solid #666;
        border-radius: 4px; 
        padding: 12px 16px; 
        margin: 8px 0; 
    }
    .chat-ai { 
        background: #111; 
        border-left: 3px solid #c9a962;
        border-radius: 4px; 
        padding: 12px 16px; 
        margin: 8px 0; 
    }
</style>
""", unsafe_allow_html=True)

# --- BUBBLE STORAGE FUNCTIONS ---
BUBBLES_FILE = "data/atom_bubbles.json"

def load_bubbles():
    if os.path.exists(BUBBLES_FILE):
        try:
            with open(BUBBLES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"bubbles": [], "last_id": 0}

def save_bubbles(data):
    with open(BUBBLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_bubble(text):
    data = load_bubbles()
    colors = ["#9333EA", "#3B82F6", "#14B8A6", "#F59E0B", "#F43F5E", "#10B981"]
    new_id = data["last_id"] + 1
    bubble = {
        "id": new_id,
        "text": text,
        "color": random.choice(colors),
        "created_at": datetime.now().isoformat(),
        "expanded": False
    }
    data["bubbles"].insert(0, bubble)
    data["last_id"] = new_id
    save_bubbles(data)
    return bubble

def delete_bubble(bubble_id):
    data = load_bubbles()
    data["bubbles"] = [b for b in data["bubbles"] if b["id"] != bubble_id]
    save_bubbles(data)

def mark_bubble_expanded(bubble_id):
    data = load_bubbles()
    for b in data["bubbles"]:
        if b["id"] == bubble_id:
            b["expanded"] = True
            break
    save_bubbles(data)

def expand_bubble_with_crew(bubble_text):
    if not CREW_AVAILABLE:
        return None, "CrewAI tidak tersedia"
    
    try:
        result = run_research_crew(f"Research and write about: {bubble_text}")
        note = create_note(
            title=f"📝 {bubble_text[:40]}...",
            content=result,
            tags=["bubble-expanded", "crewai"],
            note_type="note"
        )
        return note, None
    except Exception as e:
        return None, str(e)


# --- SESSION STATE ---
if "current_note_id" not in st.session_state:
    st.session_state.current_note_id = None
if "note_mode" not in st.session_state:
    st.session_state.note_mode = "view"
if "note_chat_history" not in st.session_state:
    st.session_state.note_chat_history = []
if "edit_content" not in st.session_state:
    st.session_state.edit_content = ""


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 📚 Smart Notes")
    
    # Tab selector
    tab_choice = st.radio(
        "Mode",
        ["📝 Notes", "🫧 Bubbles"],
        horizontal=True,
        label_visibility="collapsed"
    )
    is_bubbles_tab = "Bubbles" in tab_choice
    
    st.markdown("---")
    
    if not is_bubbles_tab:
        if st.button("➕ New Note", use_container_width=True):
            new_note = create_note(title="Untitled Note", content="", tags=[])
            st.session_state.current_note_id = new_note["id"]
            st.session_state.note_mode = "edit"
            st.session_state.edit_content = ""
            st.rerun()
        
        st.markdown("---")
        
        search_query = st.text_input("🔍 Search", placeholder="Search notes...")
        
        all_tags = get_all_tags()
        selected_tag = st.selectbox("Filter", ["All"] + all_tags) if all_tags else "All"
        
        st.markdown("---")
        
        notes = search_notes(search_query) if search_query else get_all_notes()
        if selected_tag != "All":
            notes = [n for n in notes if selected_tag in n.get("tags", [])]
        
        for note in notes[:10]:  # Limit to 10 for performance
            is_selected = st.session_state.current_note_id == note["id"]
            col1, col2 = st.columns([5, 1])
            with col1:
                btn_label = f"{'▶ ' if is_selected else ''}{note['title'][:20]}"
                if st.button(btn_label, key=f"note_{note['id']}", use_container_width=True):
                    st.session_state.current_note_id = note["id"]
                    st.session_state.note_mode = "view"
                    st.session_state.note_chat_history = []
                    st.session_state.edit_content = note.get("content", "")
                    st.rerun()
            with col2:
                if st.button("🗑", key=f"del_{note['id']}"):
                    delete_note(note["id"])
                    if st.session_state.current_note_id == note["id"]:
                        st.session_state.current_note_id = None
                    st.rerun()
    
    st.markdown("---")
    stats = get_stats()
    st.caption(f"📊 {stats['total_notes']} notes | {stats['total_tags']} tags")
    st.page_link("ATOM_Chat.py", label="← Back to Chat")


# === MAIN CONTENT ===

if is_bubbles_tab:
    # ========== BUBBLES TAB ==========
    st.markdown("## 🫧 Floating Bubbles")
    st.caption("Quick ideas that can expand into full articles via CrewAI")
    
    # Add new bubble
    col1, col2 = st.columns([5, 1])
    with col1:
        new_bubble_text = st.text_input(
            "💡",
            placeholder="Type a quick idea (1-2 sentences)...",
            label_visibility="collapsed"
        )
    with col2:
        add_btn = st.button("🫧 Add", use_container_width=True)
    
    if add_btn and new_bubble_text and new_bubble_text.strip():
        add_bubble(new_bubble_text.strip())
        st.rerun()
    
    st.markdown("---")
    
    # Load bubbles
    bubbles_data = load_bubbles()
    bubbles = bubbles_data.get("bubbles", [])
    
    if not bubbles:
        st.info("No bubbles yet. Add your first quick idea above! 🫧")
    else:
        # Display bubbles in a cleaner grid
        for bubble in bubbles:
            color = bubble.get('color', '#9333EA')
            created = bubble.get('created_at', '')[:10]
            is_expanded = bubble.get('expanded', False)
            
            # Create a styled container for each bubble
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}40, {color}20);
                border: 1px solid {color}60;
                border-radius: 16px;
                padding: 16px 20px;
                margin-bottom: 12px;
            ">
                <div style="color: #fff; font-size: 15px; line-height: 1.5; margin-bottom: 8px;">
                    {bubble['text']}
                </div>
                <div style="color: #888; font-size: 11px;">
                    {created} {'✨ Expanded' if is_expanded else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons below each bubble
            col_a, col_b, col_c = st.columns([2, 2, 6])
            with col_a:
                if not is_expanded:
                    if st.button("🚀 Expand", key=f"exp_{bubble['id']}", use_container_width=True):
                        with st.spinner("CrewAI sedang riset & menulis..."):
                            note, error = expand_bubble_with_crew(bubble['text'])
                            if note:
                                mark_bubble_expanded(bubble['id'])
                                st.success("🎉 Bubble → Article!")
                                st.balloons()
                            else:
                                st.error(f"Error: {error}")
                        st.rerun()
                else:
                    st.caption("✅ Done")
            
            with col_b:
                if st.button("🗑 Delete", key=f"delbub_{bubble['id']}", use_container_width=True):
                    delete_bubble(bubble['id'])
                    st.rerun()

else:
    # ========== NOTES TAB ==========
    if st.session_state.current_note_id:
        note = get_note(st.session_state.current_note_id)
        
        if note:
            # Header
            st.markdown(f"### {note['title']}")
            
            # Mode Switcher
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("👁 View", use_container_width=True, 
                           type="primary" if st.session_state.note_mode == "view" else "secondary"):
                    st.session_state.note_mode = "view"
                    st.rerun()
            with col2:
                if st.button("✏️ Edit", use_container_width=True,
                           type="primary" if st.session_state.note_mode == "edit" else "secondary"):
                    st.session_state.note_mode = "edit"
                    st.session_state.edit_content = note.get("content", "")
                    st.rerun()
            with col3:
                if st.button("💬 Chat", use_container_width=True,
                           type="primary" if st.session_state.note_mode == "chat" else "secondary"):
                    st.session_state.note_mode = "chat"
                    st.rerun()
            
            # Tags
            if note.get("tags"):
                st.markdown(" ".join([f'<span class="tag">{t}</span>' for t in note["tags"]]), unsafe_allow_html=True)
            
            st.markdown("---")
            
            # === VIEW MODE ===
            if st.session_state.note_mode == "view":
                st.markdown(note["content"] or "*Empty note*")
                st.caption(f"Created: {note.get('created_at', '')[:16]}")
            
            # === EDIT MODE ===
            elif st.session_state.note_mode == "edit":
                new_title = st.text_input("Title", value=note["title"])
                
                col_edit, col_magic = st.columns([4, 1])
                with col_magic:
                    if st.button("✨ Rapihkan"):
                        if st.session_state.edit_content:
                            with st.spinner("AI merapihkan..."):
                                refined = refine_text(st.session_state.edit_content)
                                st.session_state.edit_content = refined
                                st.rerun()
                
                new_content = st.text_area(
                    "Content (Markdown)", 
                    value=st.session_state.edit_content, 
                    height=300
                )
                st.session_state.edit_content = new_content
                
                tags_str = ", ".join(note.get("tags", []))
                new_tags_str = st.text_input("Tags (comma separated)", value=tags_str)
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("💾 Save", type="primary", use_container_width=True):
                        new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
                        update_note(note["id"], title=new_title, content=new_content, tags=new_tags)
                        st.success("Saved!")
                        st.session_state.note_mode = "view"
                        st.rerun()
                with col2:
                    if st.button("🤖 Auto-Tag"):
                        if new_content:
                            with st.spinner("Generating..."):
                                auto_tags = auto_tag(new_content)
                                if auto_tags:
                                    st.info(f"Suggested: {', '.join(auto_tags)}")
            
            # === CHAT MODE ===
            elif st.session_state.note_mode == "chat":
                st.markdown("**Chat with this note** - AI answers based on note content only")
                
                for msg in st.session_state.note_chat_history:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
                
                question = st.chat_input("Ask about this note...")
                
                if question:
                    st.session_state.note_chat_history.append({"role": "user", "content": question})
                    with st.spinner("Thinking..."):
                        response = chat_with_context(note["content"], question)
                    st.session_state.note_chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
                
                if st.session_state.note_chat_history:
                    if st.button("🗑 Clear Chat"):
                        st.session_state.note_chat_history = []
                        st.rerun()
                
                with st.expander("📄 Note Content"):
                    st.markdown(note["content"] or "*Empty*")

    else:
        st.markdown("## 📚 Smart Notes")
        st.markdown("*Select a note from sidebar or create new*")
        
        stats = get_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Notes", stats["total_notes"])
        with col2:
            st.metric("Tags", stats["total_tags"])
        with col3:
            st.metric("Chat Logs", stats["by_type"].get("chat_log", 0))
        
        st.markdown("---")
        st.markdown("### Recent Notes")
        for note in get_all_notes()[:5]:
            if st.button(f"📝 {note['title']}", key=f"recent_{note['id']}"):
                st.session_state.current_note_id = note["id"]
                st.rerun()
