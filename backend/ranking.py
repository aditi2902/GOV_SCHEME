"""
Agent 4: Ranking Agent
Scores and ranks schemes based on multiple factors.
NO LLM calls — pure algorithmic scoring.
"""

import pandas as pd


# ── Benefit Type Weights ───────────────────────────────

BENEFIT_TYPE_SCORES = {
    "fellowship": 18,
    "scholarship": 15,
    "internship": 14,
    "stipend": 12,
    "grant": 10,
    "travel_grant": 8,
    "loan": 5,
    "subsidy": 6,
    "training": 7,
}


def score_scheme(row: pd.Series, match_score: float = 100.0) -> float:
    """
    Score a scheme for ranking.

    Factors:
    1. Benefit amount (higher = better), capped contribution
    2. Benefit type (scholarship > loan)
    3. Eligibility match score (from eligibility engine)
    4. Central vs State (central schemes = wider applicability)

    Args:
        row: scheme row from DataFrame
        match_score: eligibility match score from eligibility engine (0-100)

    Returns:
        float score (higher = better recommendation)
    """

    score = 0.0

    # ── Factor 1: Benefit Amount (0–25 points) ─────
    if pd.notna(row.get("benefit_amount")):
        amount = float(row["benefit_amount"])
        # Log-scale so ₹50k and ₹5L don't differ by 10x
        if amount > 0:
            import math
            score += min(math.log10(amount) * 5, 25)

    # ── Factor 2: Benefit Type (0–18 points) ───────
    if pd.notna(row.get("benefit_type")):
        btype = str(row["benefit_type"]).strip().lower()
        # Handle comma-separated types
        types = [t.strip() for t in btype.split(",")]
        type_score = max(
            BENEFIT_TYPE_SCORES.get(t, 3)
            for t in types
        )
        score += type_score

    # ── Factor 3: Match Score (0–30 points) ────────
    score += (match_score / 100) * 30

    # ── Factor 4: Central vs State (0–5 points) ────
    if pd.notna(row.get("level")):
        if str(row["level"]).strip().lower() == "central":
            score += 5
        else:
            score += 3

    # ── Factor 5: Has clear application process ────
    if pd.notna(row.get("application")):
        app_text = str(row["application"])
        if len(app_text) > 50:
            score += 5  # Well-documented application = easier to apply

    return round(score, 2)