"""
Agent 5: Document Agent
Parses required documents from scheme data and checks readiness.
Pure rule-based — NO LLM calls.
"""

import pandas as pd
import re


# ── Common Document Aliases ────────────────────────────
# Maps various document name patterns to standardized names

DOCUMENT_PATTERNS = {
    r"aadh[a]*r": "Aadhaar Card",
    r"income\s*certificate": "Income Certificate",
    r"caste\s*certificate": "Caste Certificate",
    r"domicile": "Domicile Certificate",
    r"mark\s*sheet|marks\s*card": "Marksheets / Transcripts",
    r"10th|ssc|secondary": "10th Certificate & Marksheet",
    r"12th|hsc|senior\s*secondary": "12th Certificate & Marksheet",
    r"bonafide|bona\s*fide|study\s*certificate": "Bonafide / Study Certificate",
    r"bank\s*(account|passbook|details)": "Bank Account Details / Passbook",
    r"passport\s*size\s*photo": "Passport Size Photograph",
    r"fee\s*receipt": "Fee Receipt",
    r"admission\s*letter|admission\s*proof": "Admission Letter",
    r"disability\s*certificate|pwd\s*certificate": "Disability Certificate (PwD)",
    r"minority\s*certificate": "Minority Certificate",
    r"ration\s*card": "Ration Card",
    r"voter\s*id": "Voter ID",
    r"pan\s*card|pan": "PAN Card",
    r"birth\s*certificate": "Birth Certificate",
    r"diploma\s*certificate": "Diploma Certificate",
    r"iti\s*certificate": "ITI Certificate",
    r"community\s*certificate": "Community Certificate",
    r"first\s*graduate": "First Graduate Certificate",
    r"self[\s-]*declaration|self[\s-]*attested": "Self-Declaration Form",
    r"annual\s*family\s*income": "Annual Family Income Certificate",
    r"ewsclass\s*certificate|ews\s*certificate": "EWS Certificate",
}


def parse_documents(doc_text: str) -> list[str]:
    """
    Extract individual document names from the scheme's
    documents column text.

    Returns a list of standardized document names.
    """

    if not doc_text or pd.isna(doc_text):
        return []

    doc_text_lower = doc_text.lower()
    found = []

    for pattern, name in DOCUMENT_PATTERNS.items():
        if re.search(pattern, doc_text_lower):
            if name not in found:
                found.append(name)

    # If we couldn't parse any known patterns, return raw split
    if not found and len(doc_text) > 10:
        # Try splitting by common delimiters
        raw = re.split(r"[;,\n]|\d+\.", doc_text)
        for item in raw:
            item = item.strip()
            if 5 < len(item) < 100:
                found.append(item)

    return found


def check_documents(
    scheme: pd.Series,
    user_profile: dict,
) -> dict:
    """
    Check document readiness for a scheme.

    Args:
        scheme: row from the schemes DataFrame
        user_profile: user's profile dict

    Returns:
        {
            "scheme_name": str,
            "required": [str],
            "common_documents": [str],
            "readiness_tip": str,
        }
    """

    doc_text = scheme.get("documents", "")
    required = parse_documents(str(doc_text))

    # Always-needed documents for most schemes
    universal = ["Aadhaar Card", "Bank Account Details / Passbook"]
    common = []
    for doc in universal:
        if doc not in required:
            common.append(doc)

    # Add context-specific documents
    if user_profile.get("category") and user_profile["category"] not in ("General", None):
        if "Caste Certificate" not in required:
            common.append("Caste Certificate")

    if user_profile.get("disability"):
        if "Disability Certificate (PwD)" not in required:
            common.append("Disability Certificate (PwD)")

    if user_profile.get("minority"):
        if "Minority Certificate" not in required:
            common.append("Minority Certificate")

    # Generate a readiness tip
    tips = []
    if "Income Certificate" in required:
        tips.append(
            "Get income certificate from your Tehsildar / SDM office. "
            "Takes 7-15 days."
        )
    if "Domicile Certificate" in required:
        tips.append(
            "Domicile certificate can be obtained from your "
            "district collector's office."
        )
    if "Bonafide / Study Certificate" in required:
        tips.append(
            "Request bonafide certificate from your college/university."
        )

    readiness_tip = " | ".join(tips) if tips else "Keep all documents ready in PDF format."

    return {
        "scheme_name": scheme.get("scheme_name", "Unknown"),
        "required": required,
        "common_documents": common,
        "readiness_tip": readiness_tip,
    }
