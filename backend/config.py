"""
Centralized configuration for the Government Scheme Platform.
Loads settings from environment variables / .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"

# ── Load .env ──────────────────────────────────────────
load_dotenv(BASE_DIR / ".env")

# ── Gemini ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Data files ─────────────────────────────────────────
SCHEMES_CSV = BASE_DIR / "processed_student_schemes.csv"

# ── ChromaDB ───────────────────────────────────────────
CHROMA_DIR = str(DATA_DIR / "chroma_db")
CHROMA_COLLECTION = "schemes"

# ── Server ─────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")
