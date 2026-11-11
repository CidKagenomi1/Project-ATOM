class Librarian:
    """The Librarian: In-memory conversation context management."""
    def __init__(self):
        self.raw_history = []
        self.summary = ""
    
    def add_interaction(self, user, ai):
        self.raw_history.append(f"User: {user}")
        self.raw_history.append(f"ATOM: {ai}")
        if len(self.raw_history) > 8:
            self.raw_history = self.raw_history[-6:]
            
    def get_context(self):
        return "\n".join(self.raw_history)
    
    def clear(self):
        self.raw_history = []
        self.summary = ""

