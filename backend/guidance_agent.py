"""
Agent 6: Guidance Agent
Uses Gemini to generate personalized step-by-step application roadmaps.
"""

import json
import re
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL


client = genai.Client(api_key=GEMINI_API_KEY)


def generate_guidance(
    profile: dict,
    eligible_schemes: list[dict],
    document_checklists: list[dict],
) -> str:
    """
    Generate a personalized application roadmap.

    Args:
        profile: user's structured profile
        eligible_schemes: list of eligible scheme dicts (top N)
        document_checklists: document readiness info per scheme

    Returns:
        Markdown-formatted guidance string
    """

    # Limit to top 5 schemes to keep prompt manageable
    top_schemes = eligible_schemes[:5]
    top_docs = document_checklists[:5]

    prompt = f"""
You are a helpful government scheme advisor for Indian citizens.

Based on the user's profile and their eligible schemes, generate a
clear, actionable, step-by-step application roadmap.

USER PROFILE:
{json.dumps(profile, indent=2, default=str)}

TOP ELIGIBLE SCHEMES:
{json.dumps(top_schemes, indent=2, default=str)}

DOCUMENT REQUIREMENTS:
{json.dumps(top_docs, indent=2, default=str)}

Generate a roadmap with:
1. Which scheme to apply for FIRST (based on benefit amount and ease)
2. What documents to gather first (prioritize shared documents)
3. Step-by-step application instructions
4. Timeline estimate
5. Pro tips (common mistakes to avoid)

Format as clean markdown with headers and bullet points.
Keep it practical and actionable. Use ₹ for currency.
Respond in English.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text.strip()


def generate_comparison(
    profile: dict,
    schemes: list[dict],
) -> str:
    """
    Generate a detailed comparison of schemes using Gemini.

    Args:
        profile: user's profile
        schemes: list of scheme dicts to compare

    Returns:
        Markdown-formatted comparison
    """

    prompt = f"""
You are a government scheme advisor. Compare the following schemes
for this user and recommend the best option.

USER PROFILE:
{json.dumps(profile, indent=2, default=str)}

SCHEMES TO COMPARE:
{json.dumps(schemes, indent=2, default=str)}

Provide:
1. Side-by-side comparison table (benefit amount, eligibility, documents)
2. Pros and cons of each
3. Your recommendation based on the user's profile
4. Which to apply for first

Format as clean markdown. Use ₹ for amounts.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text.strip()
