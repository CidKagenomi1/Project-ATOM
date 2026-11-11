import os
import sys
import uvicorn
from fastapi.staticfiles import StaticFiles

# Add current folder to path to load api modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from api.index import app
except ImportError as e:
    print(f"Error loading API app: {e}")
    sys.exit(1)

# Serve static files from 'public' directory at root
app.mount("/", StaticFiles(directory="public", html=True), name="public")

if __name__ == "__main__":
    import socket

    def is_port_in_use(port_num: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port_num)) == 0

    port = int(os.getenv("PORT", 8000))
    if "PORT" not in os.environ and is_port_in_use(port):
        print(f"[!] Port {port} sedang digunakan oleh aplikasi lain.")
        port = 8080 if not is_port_in_use(8080) else 8001
        print(f"[*] Mengalihkan otomatis ke port {port}...")

    print(f"Starting dev server on port {port}...")
    print(f"[*] ATOM Local Dev Server ready at http://localhost:{port}")
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("dev_server:app", host=host, port=port, reload=True)

