"""
ATOM Smart Notes - Brain Module
AI-powered functions for note intelligence.
Uses LangChain + Groq (Llama-3.3-70B)
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def _get_llm(temperature: float = 0.3):
    """Get Groq LLM instance."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=temperature
    )


# === CHAT WITH CONTEXT ===

def chat_with_context(context_text: str, question: str) -> str:
    """
    Answer a question based ONLY on the provided context.
    Like NotebookLLM - grounded responses.
    
    Args:
        context_text: The note content to use as context
        question: User's question about the context
        
    Returns:
        AI-generated answer grounded in the context
    """
    if not context_text or not question:
        return "Context atau pertanyaan tidak boleh kosong."
    
    try:
        llm = _get_llm(temperature=0.2)
        
        system_prompt = SystemMessage(content="""
        You are ATOM's Knowledge Assistant.
        
        RULES:
        1. Answer the user's question ONLY based on the provided CONTEXT.
        2. If the answer is not in the context, say "Informasi tersebut tidak ada dalam catatan ini."
        3. Be concise and direct.
        4. Use Indonesian language.
        5. Quote relevant parts from the context when helpful.
        """)
        
        user_prompt = HumanMessage(content=f"""
        CONTEXT (Isi Catatan):
        ---
        {context_text}
        ---
        
        PERTANYAAN: {question}
        
        Jawab berdasarkan CONTEXT di atas:
        """)
        
        response = llm.invoke([system_prompt, user_prompt])
        return response.content
        
    except Exception as e:
        return f"[ERROR] Gagal memproses: {str(e)}"


# === MAGIC ARTICLE FORMATTER ===

def refine_text(raw_text: str) -> str:
    """
    Clean up messy copy-pasted text into well-structured markdown article.
    
    Args:
        raw_text: Messy/unformatted text from internet
        
    Returns:
        Clean, structured markdown article
    """
    if not raw_text or len(raw_text.strip()) < 20:
        return raw_text
    
    try:
        llm = _get_llm(temperature=0.3)
        
        system_prompt = SystemMessage(content="""
        Kamu adalah Editor Artikel Profesional.
        
        Tugasmu adalah menerima teks mentah yang berantakan, lalu menyusunnya ulang menjadi 
        Artikel Markdown yang rapi, terstruktur (Heading, Bullet points), enak dibaca, 
        dan memperbaiki typo, TANPA mengurangi informasi penting.
        
        ATURAN:
        1. Gunakan heading (##, ###) untuk struktur
        2. Gunakan bullet points untuk list
        3. Perbaiki typo dan tata bahasa
        4. Pertahankan semua informasi penting
        5. Buat paragraf yang rapi
        6. Jangan tambahkan informasi baru
        7. Jika ada bahasa campuran, pertahankan bahasa aslinya
        """)
        
        user_prompt = HumanMessage(content=f"""
        TEKS MENTAH:
        ---
        {raw_text[:4000]}
        ---
        
        Rapihkan teks di atas menjadi artikel Markdown yang terstruktur:
        """)
        
        response = llm.invoke([system_prompt, user_prompt])
        return response.content
        
    except Exception as e:
        return f"[ERROR] Gagal merapihkan: {str(e)}"


# === AUTO TAGGING ===

def auto_tag(text: str) -> List[str]:
    """
    Automatically generate 3-5 relevant tags from text content.
    
    Args:
        text: The note content to analyze
        
    Returns:
        List of generated tags
    """
    if not text or len(text.strip()) < 10:
        return []
    
    try:
        llm = _get_llm(temperature=0.1)
        
        prompt = f"""
        Analyze this text and generate 3-5 relevant tags/keywords.
        
        TEXT:
        {text[:2000]}
        
        RULES:
        - Tags should be single words or short phrases (max 2 words)
        - Tags should capture the main topics/themes
        - Use lowercase
        - Return ONLY the tags, one per line, no numbering
        
        TAGS:
        """
        
        response = llm.invoke(prompt)
        
        # Parse tags from response
        tags = []
        for line in response.content.strip().split('\n'):
            tag = line.strip().strip('-').strip('•').strip()
            if tag and len(tag) < 30:
                tags.append(tag.lower())
        
        return tags[:5]  # Max 5 tags
        
    except Exception as e:
        print(f"[AUTO_TAG ERROR] {e}")
        return []


# === SUMMARIZE CONVERSATION ===

def summarize_conversation(messages: List[Dict[str, Any]]) -> str:
    """
    Convert a chat conversation into a structured markdown note.
    
    Args:
        messages: List of chat messages with 'role' and 'content' keys
        
    Returns:
        Structured markdown summary
    """
    if not messages or len(messages) < 2:
        return "Tidak ada percakapan untuk dirangkum."
    
    # Build conversation text
    conversation = ""
    for msg in messages:
        role = "User" if msg.get("role") == "user" else "ATOM"
        content = msg.get("content", "")
        if content:
            conversation += f"{role}: {content}\n\n"
    
    if not conversation.strip():
        return "Percakapan kosong."
    
    try:
        llm = _get_llm(temperature=0.3)
        
        prompt = f"""
        Summarize this conversation into a structured markdown note.
        
        CONVERSATION:
        {conversation[:4000]}
        
        Create a well-organized summary with:
        1. A brief title suggestion (## Title)
        2. Key points discussed (bullet points)
        3. Any conclusions or action items
        4. Use Indonesian language
        
        FORMAT:
        ## [Suggested Title]
        
        ### Ringkasan
        [2-3 sentence overview]
        
        ### Poin Penting
        - point 1
        - point 2
        
        ### Kesimpulan/Action Items
        - item 1
        
        SUMMARY:
        """
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        # Fallback: return raw conversation
        return f"## Chat Log\n\n{conversation}"


# === GENERATE TITLE ===

def generate_title(content: str) -> str:
    """Generate a concise title for note content."""
    if not content or len(content) < 10:
        return "Untitled Note"
    
    try:
        llm = _get_llm(temperature=0.2)
        
        prompt = f"""
        Generate a short, descriptive title (max 6 words) for this content:
        
        {content[:500]}
        
        Return ONLY the title, no quotes or extra formatting.
        Use Indonesian if the content is in Indonesian.
        
        TITLE:
        """
        
        response = llm.invoke(prompt)
        title = response.content.strip().strip('"').strip("'")
        
        # Limit length
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title if title else "Untitled Note"
        
    except:
        return "Untitled Note"


# === EXTRACT KEY CONCEPTS ===

def extract_concepts(text: str) -> List[Dict[str, str]]:
    """
    Extract key concepts/terms from text with brief explanations.
    Useful for building knowledge graph.
    """
    if not text or len(text) < 50:
        return []
    
    try:
        llm = _get_llm(temperature=0.2)
        
        prompt = f"""
        Extract 3-5 key concepts from this text. For each concept, provide a brief definition.
        
        TEXT:
        {text[:2000]}
        
        Format each as:
        CONCEPT: [name]
        DEFINITION: [brief explanation]
        
        OUTPUT:
        """
        
        response = llm.invoke(prompt)
        
        concepts = []
        current = {}
        
        for line in response.content.strip().split('\n'):
            line = line.strip()
            if line.startswith("CONCEPT:"):
                if current:
                    concepts.append(current)
                current = {"name": line[8:].strip(), "definition": ""}
            elif line.startswith("DEFINITION:"):
                if current:
                    current["definition"] = line[11:].strip()
        
        if current and current.get("name"):
            concepts.append(current)
        
        return concepts[:5]
        
    except Exception as e:
        print(f"[CONCEPT ERROR] {e}")
        return []
