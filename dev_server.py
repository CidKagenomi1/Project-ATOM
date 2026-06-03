import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add current folder to path to load api modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.chat import handler as ChatHandler
    from api.notes_ai import handler as NotesAIHandler
except ImportError as e:
    print(f"Error loading API handlers: {e}")
    sys.exit(1)

class AtomDevHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from 'public' directory
        super().__init__(*args, directory="public", **kwargs)

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._set_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        if self.path.startswith("/api/chat"):
            ChatHandler.do_OPTIONS(self)
        elif self.path.startswith("/api/notes_ai"):
            NotesAIHandler.do_OPTIONS(self)
        else:
            super().do_OPTIONS()

    def do_POST(self):
        if self.path.startswith("/api/chat"):
            ChatHandler.do_POST(self)
        elif self.path.startswith("/api/notes_ai"):
            NotesAIHandler.do_POST(self)
        else:
            self.send_error(404, "Not Found")

if __name__ == "__main__":
    port = 3000
    print(f"Starting dev server on port 3000...")
    server = HTTPServer(("localhost", port), AtomDevHandler)
    print(f"[*] ATOM Local Dev Server ready at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()
