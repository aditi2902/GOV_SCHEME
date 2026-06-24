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
import re


# Education level → typical max age for schemes targeting that level
_EDU_AGE_LIMITS = {
    "school": 19,
    "iti":    25,
    "diploma": 25,
    "ug":     30,
    "pg":     35,
    "phd":    40,
}

# Education hierarchy for progressive matching (higher rank = higher education)
EDUCATION_RANK = {
    "school": 1,
    "iti": 2,
    "diploma": 3,
    "ug": 4,
    "pg": 5,
    "phd": 6,
}

# Keyword patterns that signal a minimum education level is required
# Each entry: (regex_pattern, minimum_education_level_key)
_EDU_KEYWORD_GUARDS = [
    # PhD / Doctoral level
    (r'\bph\.?d\.?\b|\bdoctoral\b|\bpostdoctoral\b|\bpost-doctoral\b|\bd\.?sc\.?\b', 'phd'),
    # Medical degrees implying PhD level
    (r'\bm\.?d\.\b|\bm\.?s\.\b.*\bdegree\b|\bm\.?d\.\s*/\s*m\.?s', 'phd'),
    # PG level
    (r'\bpostgraduate\b|\bpost.graduate\b|\bm\.tech\b|\bm\.?e\.?\b|\bmba\b|\bmca\b|\bm\.?sc\.?\b|\bm\.?a\.?\b|\bm\.?com\.?\b', 'pg'),
]


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

    # ── Free-text Education Keyword Guard ─────────────
    # When the structured education_level column is missing/null, scan the
    # free-text eligibility field for PhD/PG keywords to catch schemes where
    # the degree requirement is only written in the description.
    if pd.isna(scheme.get("education_level")) and pd.notna(scheme.get("eligibility")):
        eligibility_text = str(scheme["eligibility"]).lower()
        user_edu_key = str(user.get("education_level", "") or "").strip().lower()
        user_edu_rank = EDUCATION_RANK.get(user_edu_key, 0)

        for pattern, required_level in _EDU_KEYWORD_GUARDS:
            if re.search(pattern, eligibility_text, re.IGNORECASE):
                required_rank = EDUCATION_RANK.get(required_level, 0)
                if user_edu_rank < required_rank:
                    reasons.append(
                        f"This scheme requires a {required_level.upper()} degree; "
                        f"your education level ({user.get('education_level', 'not specified')}) does not meet this requirement."
                    )
                break  # Only apply the highest-level guard found

    # ── Age / Education-level bracket ──────────────
    # Use scheme's education_level to infer a realistic age cap.
    user_age = user.get("age")
    scheme_edu_raw = scheme.get("education_level")

    if pd.notna(scheme_edu_raw) and user_age is not None:
        scheme_edu_key = str(scheme_edu_raw).strip().lower()
        age_cap = _EDU_AGE_LIMITS.get(scheme_edu_key)
        if age_cap and user_age > age_cap:
            reasons.append(
                f"Age {user_age} is too high for a {scheme_edu_raw}-level scheme "
                f"(typically for students up to {age_cap} years old)"
            )

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
            # Gender not provided — give partial credit (don't reject outright)
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