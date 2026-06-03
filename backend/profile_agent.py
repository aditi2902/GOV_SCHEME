"""
Agent 1: Profile Understanding Agent
Extracts structured user profile from free-text description using Gemini.
"""

import json
import re
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


# ── Gemini Client ──────────────────────────────────────

client = genai.Client(api_key=GEMINI_API_KEY)


# ── Profile Extraction ─────────────────────────────────

def extract_profile(user_text: str) -> dict:
    """
    Parse unstructured user text into a structured profile dict.

    Returns dict with keys:
        state, income, gender, age, education_level, course,
        year_of_study, cgpa, category, disability, minority
    """

    prompt = f"""
You are a profile extraction agent for Indian government schemes.
Extract the following fields from the user's description.
Return ONLY valid JSON, no markdown, no explanation.

Fields:
- state (string or null) — Indian state name
- income (number or null) — annual family income in INR
- gender (string or null) — "male" or "female" or "other"
- age (integer or null) — age in years
- education_level (string or null) — one of: "10th", "12th", "ITI", "Diploma", "UG", "PG", "PhD"
- course (string or null) — e.g. "Engineering", "Medical", "Arts"
- year_of_study (integer or null)
- cgpa (number or null) — on a 10-point scale
- category (string or null) — one of: "General", "OBC", "SC", "ST", "EWS"
- disability (boolean) — default false
- minority (boolean) — default false

Important:
- Convert "lakh" to actual number (e.g. "4 lakh" = 400000)
- Normalize state names to title case (e.g. "maharashtra" → "Maharashtra")
- If CGPA is on percentage scale (>10), convert: percentage/10
- If info is not mentioned, use null (not "unknown")

User Description:
{user_text}
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    text = response.text.strip()

    # Strip markdown code fences if present
    text = re.sub(r"```json\s*|```\s*", "", text).strip()

    profile = json.loads(text)

    # Ensure all expected keys exist with defaults
    defaults = {
        "state": None,
        "income": None,
        "gender": None,
        "age": None,
        "education_level": None,
        "course": None,
        "year_of_study": None,
        "cgpa": None,
        "category": None,
        "disability": False,
        "minority": False,
    }

    for key, default in defaults.items():
        if key not in profile:
            profile[key] = default

    return profile