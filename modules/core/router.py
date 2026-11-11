class NeuralRouter:
    """The Dispatcher: Fast keyword and heuristic routing for queries."""
    def __init__(self, crew_available: bool = True):
        self.crew_available = crew_available
    
    def decide_route(self, user_input: str) -> str:
        txt = user_input.lower().strip()
        
        # If question or conceptual exploration, direct to AI / Knowledge route
        question_words = [
            "bagaimana", "jelaskan", "apa itu", "mengapa", "kenapa",
            "ceritakan", "siapa", "how", "what is", "why"
        ]
        is_question = any(q in txt for q in question_words) or txt.endswith("?")
        
        if not is_question:
            action_kw = [
                "buka notepad", "buka calculator", "buka spotify",
                "buka browser", "buka youtube", "cek baterai",
                "matikan laptop", "restart"
            ]
            if any(kw in txt for kw in action_kw):
                return "ACTION"
        
        crew_kw = ["riset mendalam:", "deep research:", "investigasi komprehensif:"]
        if self.crew_available and any(kw in txt for kw in crew_kw):
            return "CREW"
        
        return "AI"

