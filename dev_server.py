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
    port = 8000
    print(f"Starting dev server on port {port}...")
    print(f"[*] ATOM Local Dev Server ready at http://localhost:{port}")
    print(f"[*] Swagger UI documentation available at http://localhost:{port}/docs")
    uvicorn.run(app, host="127.0.0.1", port=port)
