"""
ATOM Smart Notes - UI
Obsidian + NotebookLLM Style Knowledge Management
"""

import streamlit as st
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.note_storage import (
    get_all_notes, get_note, create_note, update_note, delete_note,
    search_notes, get_all_tags, get_note_preview, get_stats
)
from modules.note_brain import (
    chat_with_context, auto_tag, summarize_conversation, generate_title, refine_text
)

st.set_page_config(
    page_title="ATOM - Smart Notes",
    page_icon="📚",
    layout="wide"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    .stApp { background-color: #0a0a0a; color: #E0E0E0; font-family: 'Inter', sans-serif; }
    
    .stTextInput input, .stTextArea textarea {
        background-color: #111 !important;
        color: #00FF9D !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    .stButton > button {
        background: #1a1a1a;
        color: #fff;
        border: 1px solid #444;
        border-radius: 6px;
    }
    .stButton > button:hover {
        border-color: #00FF9D;
        color: #00FF9D;
    }
    
    .note-title { font-weight: 600; color: #fff; }
    .tag {
        display: inline-block;
        background: #1a1a1a;
        border: 1px solid #444;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 11px;
        margin: 2px;
        color: #00FF9D;
    }
    
    .chat-user { background: #0a2a1a; border: 1px solid #00FF9D; border-radius: 12px; padding: 10px; margin: 5px 0; }
    .chat-ai { background: #1a1a2a; border: 1px solid #4a4aaa; border-radius: 12px; padding: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

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
    
    for note in notes:
        is_selected = st.session_state.current_note_id == note["id"]
        col1, col2 = st.columns([5, 1])
        with col1:
            btn_label = f"{'▶ ' if is_selected else ''}{note['title'][:25]}"
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

# --- MAIN WORKSPACE ---
if st.session_state.current_note_id:
    note = get_note(st.session_state.current_note_id)
    
    if note:
        # Mode Switcher
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"### {note['title']}")
        with col2:
            if st.button("👁 View" if st.session_state.note_mode != "view" else "✓ View"):
                st.session_state.note_mode = "view"
                st.rerun()
        with col3:
            if st.button("✏️ Edit" if st.session_state.note_mode != "edit" else "✓ Edit"):
                st.session_state.note_mode = "edit"
                st.session_state.edit_content = note.get("content", "")
                st.rerun()
        with col4:
            if st.button("💬 Chat" if st.session_state.note_mode != "chat" else "✓ Chat"):
                st.session_state.note_mode = "chat"
                st.rerun()
        
        # Tags
        if note.get("tags"):
            st.markdown(" ".join([f'<span class="tag">{t}</span>' for t in note["tags"]]), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # === VIEW MODE ===
        if st.session_state.note_mode == "view":
            st.markdown(note["content"] or "*Empty note*")
            st.caption(f"Created: {note.get('created_at', '')[:16]} | Updated: {note.get('updated_at', '')[:16]}")
        
        # === EDIT MODE ===
        elif st.session_state.note_mode == "edit":
            new_title = st.text_input("Title", value=note["title"], key="edit_title")
            
            # Content editor with Magic Formatter
            col_edit, col_magic = st.columns([4, 1])
            with col_magic:
                if st.button("✨ Rapihkan", help="AI merapihkan tulisan"):
                    if st.session_state.edit_content:
                        with st.spinner("AI sedang merapihkan..."):
                            refined = refine_text(st.session_state.edit_content)
                            st.session_state.edit_content = refined
                            st.rerun()
            
            new_content = st.text_area(
                "Content (Markdown)", 
                value=st.session_state.edit_content, 
                height=300, 
                key="content_editor"
            )
            st.session_state.edit_content = new_content
            
            # Tags
            col1, col2 = st.columns([3, 1])
            with col1:
                tags_str = ", ".join(note.get("tags", []))
                new_tags_str = st.text_input("Tags (comma separated)", value=tags_str)
            with col2:
                if st.button("🤖 Auto-Tag"):
                    if new_content:
                        with st.spinner("Generating..."):
                            auto_tags = auto_tag(new_content)
                            if auto_tags:
                                st.info(f"Suggested: {', '.join(auto_tags)}")
            
            if st.button("💾 Save", type="primary"):
                new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]
                update_note(note["id"], title=new_title, content=new_content, tags=new_tags)
                st.success("Saved!")
                st.session_state.note_mode = "view"
                st.rerun()
        
        # === CHAT MODE (NotebookLLM Style) ===
        elif st.session_state.note_mode == "chat":
            st.markdown("**Chat with this note** - AI answers based on note content only")
            
            # Chat history
            for msg in st.session_state.note_chat_history:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">🧑 {msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-ai">🤖 {msg["content"]}</div>', unsafe_allow_html=True)
            
            # Chat input with Enter to Send
            question = st.chat_input("Ask about this note...")
            
            if question:
                # Add user message
                st.session_state.note_chat_history.append({"role": "user", "content": question})
                
                # Get AI response
                with st.spinner("Thinking..."):
                    response = chat_with_context(note["content"], question)
                
                # Add AI response
                st.session_state.note_chat_history.append({"role": "assistant", "content": response})
                st.rerun()
            
            # Clear chat button
            if st.session_state.note_chat_history:
                if st.button("🗑 Clear Chat"):
                    st.session_state.note_chat_history = []
                    st.rerun()
            
            # Reference
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
    st.markdown("### Recent")
    for note in get_all_notes()[:5]:
        if st.button(f"📝 {note['title']}", key=f"recent_{note['id']}"):
            st.session_state.current_note_id = note["id"]
            st.rerun()
