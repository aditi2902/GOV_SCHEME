"""
Agent 2: Eligibility Engine
Pure Python rule-based eligibility checker.
NO LLM calls — deterministic and fast.

Returns not just pass/fail but:
- match_score (0-100)
- rejection_reasons (why not eligible)
- matched_criteria (what matched)
"""

import pandas as pd


def is_eligible(user: dict, scheme: pd.Series) -> dict:
    """
    Check if a user is eligible for a scheme.

    Returns:
        {
            "eligible": bool,
            "match_score": float (0-100),
            "rejection_reasons": [str],
            "matched_criteria": [str],
        }
    """

    reasons = []
    matched = []
    total_criteria = 0
    passed_criteria = 0

    # ── Income ─────────────────────────────────────

    if pd.notna(scheme.get("income_max")):
        total_criteria += 1

        if user.get("income") is not None:
            if user["income"] <= scheme["income_max"]:
                passed_criteria += 1
                matched.append(
                    f"Income ₹{user['income']:,.0f} within limit ₹{scheme['income_max']:,.0f}"
                )
            else:
                reasons.append(
                    f"Income ₹{user['income']:,.0f} exceeds limit ₹{scheme['income_max']:,.0f}"
                )
        else:
            # Income not provided — give benefit of doubt
            passed_criteria += 0.5

    # ── Gender ─────────────────────────────────────

    if pd.notna(scheme.get("gender")):
        total_criteria += 1
        scheme_gender = str(scheme["gender"]).strip().lower()

        if user.get("gender"):
            if user["gender"].lower() == scheme_gender:
                passed_criteria += 1
                matched.append(f"Gender matches: {scheme_gender}")
            else:
                reasons.append(
                    f"Scheme requires gender: {scheme_gender}, you are: {user['gender']}"
                )
        else:
            passed_criteria += 0.5

    # ── Category / Caste ───────────────────────────

    if pd.notna(scheme.get("category")):
        total_criteria += 1
        scheme_cats = [
            c.strip().lower()
            for c in str(scheme["category"]).split(",")
        ]

        if user.get("category"):
            if user["category"].lower() in scheme_cats:
                passed_criteria += 1
                matched.append(f"Category matches: {user['category']}")
            else:
                reasons.append(
                    f"Scheme requires category: {scheme['category']}, you are: {user['category']}"
                )
        else:
            # Not provided — don't reject
            passed_criteria += 0.5

    # ── Disability ─────────────────────────────────

    if scheme.get("disability_required"):
        total_criteria += 1

        if user.get("disability"):
            passed_criteria += 1
            matched.append("Disability requirement met")
        else:
            reasons.append("Scheme requires disability status")

    # ── Education Level ────────────────────────────

    if pd.notna(scheme.get("education_level")):
        total_criteria += 1
        scheme_edu = str(scheme["education_level"]).strip().lower()

        if user.get("education_level"):
            if user["education_level"].lower() == scheme_edu:
                passed_criteria += 1
                matched.append(f"Education level matches: {scheme_edu.upper()}")
            else:
                reasons.append(
                    f"Scheme requires education: {scheme['education_level']}, you have: {user['education_level']}"
                )
        else:
            passed_criteria += 0.5

    # ── Course ─────────────────────────────────────

    if pd.notna(scheme.get("course")):
        total_criteria += 1
        scheme_course = str(scheme["course"]).strip().lower()

        if user.get("course"):
            user_course = user["course"].lower()
            # Fuzzy match: "engineering" matches "b.tech engineering"
            if (
                user_course in scheme_course
                or scheme_course in user_course
                or user_course == scheme_course
            ):
                passed_criteria += 1
                matched.append(f"Course matches: {scheme['course']}")
            else:
                reasons.append(
                    f"Scheme requires course: {scheme['course']}, you study: {user['course']}"
                )
        else:
            passed_criteria += 0.5

    # ── CGPA ───────────────────────────────────────

    if pd.notna(scheme.get("cgpa_min")):
        total_criteria += 1

        if user.get("cgpa") is not None:
            if user["cgpa"] >= scheme["cgpa_min"]:
                passed_criteria += 1
                matched.append(
                    f"CGPA {user['cgpa']} meets minimum {scheme['cgpa_min']}"
                )
            else:
                reasons.append(
                    f"CGPA {user['cgpa']} below minimum {scheme['cgpa_min']}"
                )
        else:
            passed_criteria += 0.5

    # ── State ──────────────────────────────────────

    if pd.notna(scheme.get("state")):
        total_criteria += 1
        scheme_state = str(scheme["state"]).strip().lower()

        if user.get("state"):
            if user["state"].lower() == scheme_state:
                passed_criteria += 1
                matched.append(f"State matches: {scheme['state']}")
            else:
                reasons.append(
                    f"Scheme is for state: {scheme['state']}, you are from: {user['state']}"
                )
        else:
            passed_criteria += 0.5

    # ── Calculate Score ────────────────────────────

    if total_criteria == 0:
        # No specific criteria — open scheme, likely eligible
        match_score = 70.0
    else:
        match_score = round(
            (passed_criteria / total_criteria) * 100, 1
        )

    eligible = len(reasons) == 0

    return {
        "eligible": eligible,
        "match_score": match_score,
        "rejection_reasons": reasons,
        "matched_criteria": matched,
    }