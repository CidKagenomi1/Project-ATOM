"""
ATOM CrewAI Integration (GROQ EDITION)
Multi-agent research system using Groq LLM.
With Google Search capability via SerpAPI or fallback to Groq knowledge.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Set dummy OpenAI key to prevent CrewAI from complaining
# We're not actually using OpenAI, but CrewAI checks for it
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-not-used-using-groq-instead"

from langchain_groq import ChatGroq


def _get_llm():
    """Get Groq LLM untuk CrewAI agents."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan!")
    
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.7
    )


def run_research_crew(topic: str) -> str:
    """
    Fungsi yang dipanggil untuk riset mendalam.
    Uses Groq LLM with CrewAI agents.
    
    Args:
        topic: Topik atau pertanyaan yang akan diriset
        
    Returns:
        Hasil riset dalam bentuk string
    """
    print(f"[CREW] Activating Research Squad for: {topic}")
    
    try:
        from crewai import Agent, Task, Crew, Process
        
        llm = _get_llm()
        
        # 1. Agen Peneliti
        researcher = Agent(
            role='Senior Researcher',
            goal='Uncover key insights and facts about the topic',
            backstory='Expert analyst with deep knowledge in business, technology, and research methodology. You have access to vast knowledge.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # 2. Agen Penulis
        writer = Agent(
            role='Content Writer',
            goal='Create comprehensive, well-structured articles in Indonesian',
            backstory='Expert writer who transforms research into engaging, informative articles. Always writes in Bahasa Indonesia.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # Tugas Riset
        research_task = Task(
            description=f"""
            Lakukan riset mendalam tentang: {topic}
            
            Tugas:
            1. Identifikasi poin-poin kunci dan konsep utama
            2. Kumpulkan fakta, statistik, dan data relevan
            3. Analisis peluang dan tantangan
            4. Identifikasi best practices atau tips praktis
            
            Fokus pada informasi yang actionable dan berguna.
            Jawab dalam Bahasa Indonesia.
            """,
            agent=researcher,
            expected_output="Daftar lengkap poin-poin kunci hasil riset dalam Bahasa Indonesia"
        )
        
        # Tugas Penulisan
        writing_task = Task(
            description=f"""
            Berdasarkan hasil riset, tulis artikel lengkap tentang: {topic}
            
            Format Artikel:
            ## Judul yang Menarik
            
            ### Pendahuluan
            (Pengantar singkat tentang topik)
            
            ### Poin-Poin Utama
            (Uraikan hasil riset dengan detail)
            
            ### Tips Praktis / Langkah-Langkah
            (Berikan panduan actionable)
            
            ### Kesimpulan
            (Rangkuman dan rekomendasi)
            
            Gunakan Bahasa Indonesia yang natural dan mudah dipahami.
            """,
            agent=writer,
            expected_output="Artikel lengkap dalam format Markdown, Bahasa Indonesia"
        )

        # Bentuk Tim
        crew = Crew(
            agents=[researcher, writer],
            tasks=[research_task, writing_task],
            process=Process.sequential,
            verbose=True
        )

        # MULAI KERJA
        print("[CREW] Squad is now working...")
        result = crew.kickoff()
        print("[CREW] Mission complete!")
        
        # Handle different result types
        if hasattr(result, 'raw'):
            return str(result.raw)
        return str(result)
        
    except ImportError as e:
        print(f"[CREW] CrewAI import error: {e}")
        return _fallback_research(topic)
    except Exception as e:
        print(f"[CREW ERROR] {e}")
        return _fallback_research(topic)


def _fallback_research(topic: str) -> str:
    """
    Fallback: Use direct Groq call if CrewAI fails.
    """
    print("[FALLBACK] Using direct Groq research...")
    
    try:
        llm = _get_llm()
        
        prompt = f"""
        Kamu adalah peneliti dan penulis profesional.
        
        Tugas: Tulis artikel lengkap tentang "{topic}"
        
        Format:
        ## [Judul Menarik]
        
        ### Pendahuluan
        [Pengantar topik]
        
        ### Analisis Mendalam
        [Poin-poin utama dengan penjelasan detail]
        
        ### Tips Praktis
        [Langkah-langkah actionable]
        
        ### Kesimpulan
        [Rangkuman dan rekomendasi]
        
        Gunakan Bahasa Indonesia yang natural. Berikan informasi yang lengkap dan berguna.
        """
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        return f"[ERROR] Gagal melakukan riset: {str(e)}"


# Legacy functions untuk backward compatibility
def build_him_agent():
    """Buat satu agent ATOM."""
    from crewai import Agent
    
    system_instruction = (
        "IDENTITY:\n"
        "Kamu adalah ATOM (Autonomous Task Orchestration Machine).\n"
        "Kamu adalah asisten pribadi berteknologi tinggi.\n\n"
        "TONE & STYLE:\n"
        "1. Bicaralah dengan percaya diri dan cerdas.\n"
        "2. Gunakan Bahasa Indonesia yang natural.\n"
        "3. Jawab langsung ke inti masalah.\n"
    )

    return Agent(
        role="ATOM - Autonomous Task Orchestration Machine",
        goal="Membantu Tuan meriset, coding, dan menyusun strategi secara cerdas.",
        backstory=system_instruction,
        llm=_get_llm(),
        allow_delegation=False,
        verbose=True,
    )


def build_atom_crew(objective: str = "Bantu saya merencanakan jadwal belajar 1 minggu."):
    """Buat Crew tunggal berisi ATOM agent."""
    from crewai import Task, Crew, Process
    
    atom_agent = build_him_agent()

    planning_task = Task(
        description=f"Analisis dan buat rencana detail untuk: {objective}",
        agent=atom_agent,
        expected_output="Rencana terstruktur dengan poin-poin jelas.",
    )

    return Crew(
        agents=[atom_agent],
        tasks=[planning_task],
        process=Process.sequential,
        verbose=True,
    )


if __name__ == "__main__":
    # Test run
    result = run_research_crew("Bisnis lobster air tawar di Indonesia")
    print("\n=== HASIL ===\n")
    print(result)
