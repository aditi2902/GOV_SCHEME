"""
Orchestrator: Chains all agents into a single analysis pipeline.

Profile Agent → Eligibility Engine → Ranking → Documents → Guidance
"""

import pandas as pd
from config import SCHEMES_CSV
from profile_agent import extract_profile
from eligibility import is_eligible
from ranking import score_scheme
from document_agent import check_documents
from guidance_agent import generate_guidance


# ── Load schemes once at import time ───────────────────

_df = None


def _get_schemes() -> pd.DataFrame:
    """Lazy-load the schemes DataFrame."""
    global _df
    if _df is None:
        _df = pd.read_csv(SCHEMES_CSV)
        # Clean boolean columns
        _df["disability_required"] = _df["disability_required"].fillna(False)
    return _df


def run_analysis(user_text: str, include_guidance: bool = True) -> dict:
    """
    Run the full multi-agent analysis pipeline.

    Args:
        user_text: user's free-text description
        include_guidance: whether to generate LLM guidance (slower)

    Returns:
        Complete analysis result dict
    """

    df = _get_schemes()

    # ── Agent 1: Profile Extraction ────────────────
    profile = extract_profile(user_text)

    # ── Agent 2: Eligibility Check ─────────────────
    eligibility_results = []

    for _, scheme in df.iterrows():
        result = is_eligible(profile, scheme)
        result["scheme_name"] = scheme.get("scheme_name", "")
        result["slug"] = scheme.get("slug", "")
        result["scheme_data"] = scheme
        eligibility_results.append(result)

    # Separate eligible and ineligible
    eligible = [r for r in eligibility_results if r["eligible"]]
    ineligible = [r for r in eligibility_results if not r["eligible"]]

    # ── Agent 4: Ranking ───────────────────────────
    for r in eligible:
        r["score"] = score_scheme(
            r["scheme_data"],
            match_score=r["match_score"],
        )

    # Sort by score descending
    eligible.sort(key=lambda x: x["score"], reverse=True)

    # ── Build scheme summaries ─────────────────────
    eligible_schemes = []
    for r in eligible:
        s = r["scheme_data"]
        eligible_schemes.append({
            "scheme_name": r["scheme_name"],
            "slug": r["slug"],
            "category": str(s.get("schemeCategory", "")),
            "level": str(s.get("level", "")),
            "benefit_type": str(s.get("benefit_type", "")),
            "benefit_amount": (
                float(s["benefit_amount"])
                if pd.notna(s.get("benefit_amount"))
                else None
            ),
            "score": r["score"],
            "match_score": r["match_score"],
            "tags": str(s.get("tags", "")),
            "details_snippet": (
                str(s.get("details", ""))[:200] + "..."
                if pd.notna(s.get("details")) and len(str(s.get("details", ""))) > 200
                else str(s.get("details", ""))
            ),
        })

    # ── Agent 5: Document Checklists ───────────────
    doc_checklists = []
    for r in eligible[:10]:  # Top 10 only
        doc = check_documents(r["scheme_data"], profile)
        doc_checklists.append(doc)

    # ── Calculate aggregate stats ──────────────────
    total_benefit = sum(
        s["benefit_amount"]
        for s in eligible_schemes
        if s["benefit_amount"]
    )

    # Readiness score: % of schemes where we have full eligibility match
    full_matches = sum(1 for r in eligible if r["match_score"] >= 90)
    readiness = (
        round((full_matches / len(eligible)) * 100, 1)
        if eligible else 0
    )

    # Top rejection reasons across all schemes
    all_reasons = []
    for r in ineligible:
        all_reasons.extend(r["rejection_reasons"])

    # Count and rank rejection reasons
    from collections import Counter
    reason_counts = Counter(all_reasons)
    top_reasons = [
        reason for reason, _ in reason_counts.most_common(5)
    ]

    # ── Agent 6: Guidance (optional) ───────────────
    guidance_text = ""
    if include_guidance and eligible_schemes:
        try:
            guidance_text = generate_guidance(
                profile,
                eligible_schemes[:5],
                doc_checklists[:5],
            )
        except Exception as e:
            guidance_text = f"Guidance generation failed: {str(e)}"

    # ── Final Response ─────────────────────────────
    return {
        "profile": profile,
        "total_schemes": len(df),
        "eligible_count": len(eligible),
        "potential_annual_benefit": total_benefit,
        "readiness_score": readiness,
        "eligible_schemes": eligible_schemes,
        "top_rejection_reasons": top_reasons,
        "document_checklist": doc_checklists,
        "guidance": guidance_text,
    }


def get_scheme_detail(slug: str) -> dict | None:
    """Get full details for a single scheme by slug."""
    df = _get_schemes()
    match = df[df["slug"] == slug]

    if match.empty:
        return None

    row = match.iloc[0]
    return {
        "scheme_name": str(row.get("scheme_name", "")),
        "slug": str(row.get("slug", "")),
        "details": str(row.get("details", "")),
        "benefits": str(row.get("benefits", "")),
        "eligibility": str(row.get("eligibility", "")),
        "application": str(row.get("application", "")),
        "documents": str(row.get("documents", "")),
        "level": str(row.get("level", "")),
        "category": str(row.get("schemeCategory", "")),
        "tags": str(row.get("tags", "")),
        "income_max": (
            float(row["income_max"])
            if pd.notna(row.get("income_max"))
            else None
        ),
        "caste_category": (
            str(row["category"])
            if pd.notna(row.get("category"))
            else None
        ),
        "disability_required": bool(row.get("disability_required", False)),
        "education_level": (
            str(row["education_level"])
            if pd.notna(row.get("education_level"))
            else None
        ),
        "course": (
            str(row["course"])
            if pd.notna(row.get("course"))
            else None
        ),
        "cgpa_min": (
            float(row["cgpa_min"])
            if pd.notna(row.get("cgpa_min"))
            else None
        ),
        "benefit_type": str(row.get("benefit_type", "")),
        "benefit_amount": (
            float(row["benefit_amount"])
            if pd.notna(row.get("benefit_amount"))
            else None
        ),
        "state": (
            str(row["state"])
            if pd.notna(row.get("state"))
            else None
        ),
        "gender": (
            str(row["gender"])
            if pd.notna(row.get("gender"))
            else None
        ),
    }


def get_stats() -> dict:
    """Get dashboard statistics."""
    df = _get_schemes()

    categories = (
        df["schemeCategory"]
        .dropna()
        .value_counts()
        .to_dict()
    )

    levels = (
        df["level"]
        .dropna()
        .value_counts()
        .to_dict()
    )

    benefit_types = (
        df["benefit_type"]
        .dropna()
        .value_counts()
        .to_dict()
    )

    avg_benefit = (
        df["benefit_amount"]
        .dropna()
        .mean()
    )

    income_limited = df["income_max"].notna().sum()

    return {
        "total_schemes": len(df),
        "categories": categories,
        "levels": levels,
        "benefit_types": benefit_types,
        "avg_benefit_amount": round(float(avg_benefit), 2) if pd.notna(avg_benefit) else 0,
        "schemes_with_income_limit": int(income_limited),
    }
