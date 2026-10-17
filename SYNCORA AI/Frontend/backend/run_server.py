"""
Syncora AI - Backend Server Launcher
Run with: py run_server.py
"""

import sys
import uvicorn
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from config import settings

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"\n🚀 Starting Syncora AI Backend Server on http://{settings.HOST}:{settings.PORT} ...")
    print(f"📖 OpenAPI Swagger Documentation at: http://localhost:{settings.PORT}/docs")
    print(f"🤖 Telegram Bot Engine: {settings.TELEGRAM_BOT_NAME}\n")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
