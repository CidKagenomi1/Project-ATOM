"""
ATOM CrewAI Integration (GROQ EDITION)
Multi-agent research system using Groq LLM.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq

load_dotenv()


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
    """Fungsi yang dipanggil oleh Corntext untuk riset mendalam.
    
    Args:
        topic: Topik atau pertanyaan yang akan diriset
        
    Returns:
        Hasil riset dalam bentuk string
    """
    print("[CREW] Activating Research Squad...")
    
    try:
        llm = _get_llm()
        
        # 1. Agen Peneliti
        researcher = Agent(
            role='Senior Researcher',
            goal='Uncover key insights and facts about the topic',
            backstory='Expert analyst with deep knowledge in technology and research methodology.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # 2. Agen Penulis
        writer = Agent(
            role='Tech Writer',
            goal='Summarize findings into clear, actionable insights',
            backstory='Expert in distilling complex information into simple explanations. Writes in Indonesian.',
            llm=llm,
            verbose=True,
            allow_delegation=False
        )

        # Tugas Riset
        research_task = Task(
            description=f"""
            Lakukan riset mendalam tentang: {topic}
            
            Tugas:
            1. Identifikasi poin-poin kunci
            2. Cari fakta dan data relevan
            3. Analisis pro dan kontra jika ada
            
            Jawab dalam Bahasa Indonesia.
            """,
            agent=researcher,
            expected_output="Daftar poin-poin kunci hasil riset dalam Bahasa Indonesia"
        )
        
        # Tugas Penulisan
        writing_task = Task(
            description=f"""
            Berdasarkan hasil riset, tulis ringkasan yang mudah dipahami tentang: {topic}
            
            Format:
            - Gunakan Bahasa Indonesia
            - Buat ringkasan yang padat dan informatif
            - Sertakan rekomendasi jika relevan
            """,
            agent=writer,
            expected_output="Artikel ringkas dalam Bahasa Indonesia"
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
        
    except Exception as e:
        return f"[CREW ERROR] Misi gagal: {str(e)}"


# Legacy functions untuk backward compatibility
def build_him_agent() -> Agent:
    """Buat satu agent ATOM."""
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


def build_atom_crew(objective: str = "Bantu saya merencanakan jadwal belajar 1 minggu.") -> Crew:
    """Buat Crew tunggal berisi ATOM agent."""
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
    result = run_research_crew("Cara membuat aplikasi AI dengan Python")
    print("\n=== HASIL ===\n")
    print(result)
