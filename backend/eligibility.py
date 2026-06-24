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
# Used to infer required education level from free-text if it's higher than the structured column
_EDU_KEYWORD_GUARDS = [
    # PhD / Doctoral
    (r'\b(?:ph\.?d\.?|doctoral|postdoctoral|post-doctoral|d\.?sc\.?)\b', 'phd'),
    (r'\b(?:m\.?d\.|m\.?s\.)\b.*\bdegree\b|\bm\.?d\.\s*/\s*m\.?s\.', 'phd'),
    # PG level
    (r'\b(?:postgraduate|post-graduate|m\.tech|m\.e\.|mba|mca|m\.sc|m\.com)\b|\bmaster\'?s\s+(?:degree|program|course)\b', 'pg'),
    # UG level
    (r'\b(?:undergraduate|under-graduate|b\.tech|b\.e\.|bba|bca|b\.sc|b\.com)\b|\bbachelor\'?s\s+(?:degree|program|course)\b', 'ug'),
    # Diploma
    (r'\b(?:diploma|polytechnic)\b', 'diploma')
]

# ── Course Discipline Pattern Sets ───────────────────────────────────────
#
# Two separate sets are intentional:
#
# SCHEME_COURSE_PATTERNS — tight, context-aware regexes for scanning a scheme's
#   free-text (eligibility + details).  These require degree abbreviations or
#   degree-qualified nouns so generic words like "be", "science", "education"
#   in normal prose don't generate false positives.
#
# USER_COURSE_PATTERNS — simple regexes to identify what discipline the USER
#   is in from their course string (e.g. "Pharmacy / B.Pharm / M.Pharm").
#   These can be broad because the source is a structured dropdown, not prose.

# Used to detect which discipline a SCHEME targets from its free-text fields.
SCHEME_COURSE_PATTERNS = [
    # Engineering — must see B.Tech / M.Tech / B.E. or "engineering" + degree noun
    (r'\bb\.tech\b|\bm\.tech\b|\bb\.e\.\b|\bm\.e\.\b'
     r'|\bengineering\s+(?:student|course|program|degree|college|stream|branch|discipline)'
     r'|technical\s+(?:course|program|degree)\b', 'Engineering'),
    # Medical — MBBS/BDS/BAMS or "medical" + degree noun
    (r'\bmbbs\b|\bbds\b|\bbams\b|\bbhms\b'
     r'|\bmedical\s+(?:student|course|degree|program|college|stream)'
     r'|study\s+medicine\b', 'Medical'),
    # Law — LLB/LLM or "law" + degree noun
    (r'\bllb\b|\bllm\b'
     r'|\blaw\s+(?:student|course|degree|program|college)'
     r'|pursuing\s+law\b', 'Law'),
    # Pharmacy — B.Pharm/M.Pharm or "pharmacy" + degree noun
    (r'\bb\.pharm\b|\bm\.pharm\b'
     r'|\bpharmacy\s+(?:student|course|degree|program|college)'
     r'|pursuing\s+pharmacy\b', 'Pharmacy'),
    # Agriculture — needs course/degree context to avoid matching "agriculture department"
    (r'\bagriculture\s+(?:student|course|degree|college|program)'
     r'|\bforestry\s+(?:degree|course)'
     r'|\bhorticulture\s+(?:degree|course)'
     r'|\bb\.sc\.?\s+agri\b', 'Agriculture'),
    # Nursing / Allied Health — GNM/BNSc are specific enough
    (r'\bgnm\b|\bbnsc\b'
     r'|\bnursing\s+(?:student|course|degree|program|college)'
     r'|\bparamedical\s+(?:course|degree)\b'
     r'|\ballied\s+health\b', 'Nursing / Allied Health'),
    # Architecture — needs "architecture" + noun or B.Arch/M.Arch
    (r'\barchitecture\s+(?:student|course|degree|program)'
     r'|\bb\.arch\b|\bm\.arch\b', 'Architecture / Design'),
    # Computer Science — BCA/MCA are specific; "computer science" + noun
    (r'\bbca\b|\bmca\b'
     r'|\bcomputer\s+science\s+(?:student|course|degree|program)'
     r'|\bsoftware\s+(?:engineering|development)\s+(?:course|degree)'
     r'|\bdata\s+science\s+(?:course|degree|program)\b', 'Computer Science'),
    # Commerce / MBA — B.Com is specific; MBA + noun
    (r'\bb\.com\b'
     r'|\bmba\s+(?:student|course|program|degree)'
     r'|\bcommerce\s+(?:student|course|degree|stream)'
     r'|pursuing\s+(?:mba|b\.com)\b', 'Commerce / MBA'),
    # Science — B.Sc/M.Sc or "science" + degree noun
    (r'\bb\.sc\b|\bm\.sc\b'
     r'|\bscience\s+(?:student|degree|course|stream|program)'
     r'|\bstem\s+(?:course|degree|program)\b', 'Science'),
    # Arts / Humanities — B.A./M.A. or "arts" + degree noun (not just "arts")
    (r'\bb\.a\.\b|\bm\.a\.\b'
     r'|\barts\s+(?:student|course|degree|stream)'
     r'|\bhumanities\s+(?:student|course|degree|stream)'
     r'|\bsocial\s+science\s+(?:student|course|degree)\b', 'Arts / Humanities'),
    # Education / B.Ed — B.Ed/M.Ed or "teacher training" (not just "education")
    (r'\bb\.ed\b|\bm\.ed\b'
     r'|\bteacher\s+(?:training|education|certification)'
     r'|\bteaching\s+(?:degree|course|program)\b', 'Education / B.Ed'),
]

# Used to identify which discipline the USER's course string belongs to.
# Simpler patterns — source is a structured dropdown, not free prose.
USER_COURSE_PATTERNS = [
    (r'\bengineering\b|\bb\.?tech\b|\bb\.?e\.?\b', 'Engineering'),
    (r'\bmedical\b|\bmbbs\b|\bbds\b|\bbams\b|\bbhms\b|\bmedicine\b', 'Medical'),
    (r'\blaw\b|\bllb\b|\bllm\b|\blegal\b', 'Law'),
    (r'\bpharmacy\b|\bb\.?pharm\b|\bm\.?pharm\b', 'Pharmacy'),
    (r'\bagriculture\b|\bforestry\b|\bhorticulture\b|\bagri\b', 'Agriculture'),
    (r'\bnursing\b|\bgnm\b|\bbnsc\b|\bparamedical\b|\ballied\s+health\b', 'Nursing / Allied Health'),
    (r'\barchitecture\b|\barch\b|\bb\.?arch\b', 'Architecture / Design'),
    (r'\bcomputer\s+science\b|\bbca\b|\bmca\b|\bsoftware\b|\bdata\s+science\b', 'Computer Science'),
    (r'\bcommerce\b|\bb\.?com\b|\bmba\b|\bbusiness\b|\bfinance\b|\baccounting\b', 'Commerce / MBA'),
    (r'\bscience\b|\bb\.?sc\b|\bm\.?sc\b|\bstem\b', 'Science'),
    (r'\barts\b|\bhumanities\b|\bb\.?a\.?\b|\bm\.?a\.?\b|\bsocial\s+science\b', 'Arts / Humanities'),
    (r'\beducation\b|\bb\.?ed\b|\bm\.?ed\b|\bteacher\b|\bteaching\b', 'Education / B.Ed'),
]

# Marital status patterns → (regex, required_marital_status)
# required_marital_status values: 'widow', 'single', 'married', 'unmarried'
_MARITAL_PATTERNS = [
    (r'\bwidow\b|\bwidower\b', 'widow'),
    (r'\bunmarried\b|\bsingle girl\b|\bnot\s+(?:be\s+)?married\b|\bshould\s+not\s+(?:be\s+)?married\b', 'unmarried'),
    (r'\bmarried\b(?!\s+(?:and|or)\s+unmarried)', 'married'),
]

# Siblings patterns -> detect if scheme requires only child
_SIBLINGS_PATTERNS = [
    (r'\bonly\s+(?:girl\s+)?child\b|\bsingle\s+(?:girl\s+)?child\b', 'only_child'),
    (r'\b(?:two|2)\s+(?:children|daughters|sons)\b|\bmax(?:imum)?\s+(?:two|2)\s+children\b', 'max_two'),
]

# Institution patterns -> detect if scheme requires a government institution
_INSTITUTION_PATTERNS = [
    (r'\bgovernment\s+(?:college|school|institution|university)\b|\bgovt\.?\s+(?:college|school|institution|university)\b|\bstate\s+university\b|\baided\s+(?:college|school|institution)\b', 'gov'),
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

    # ── (Removed old Free-text Keyword Guard) ─────────
    # This logic has been merged into the main Education Level check below.

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
    
    eligibility_text_raw = str(scheme.get("eligibility", "") or "")
    details_text_raw = str(scheme.get("details", "") or "")
    full_text = f"{eligibility_text_raw} {details_text_raw}".lower()

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
    else:
        # Fallback: scan free text for category keywords if structured column is empty
        _CATEGORY_PATTERNS = {
            r'\b(?:sc|scheduled\s+caste)\b': 'sc',
            r'\b(?:st|scheduled\s+tribe|tribal)\b': 'st',
            r'\b(?:obc|other\s+backward\s+class(?:es)?)\b': 'obc',
            r'\b(?:ebc|economically\s+backward\s+class(?:es)?)\b': 'ebc',
            r'\b(?:vjnt|sbc)\b': 'vjnt/sbc',
        }
        
        detected_cats = []
        for pattern, cat_label in _CATEGORY_PATTERNS.items():
            if re.search(pattern, full_text, re.IGNORECASE):
                detected_cats.append(cat_label)
                
        # If the scheme explicitly restricts to specific reserved categories
        if detected_cats:
            total_criteria += 1
            if user.get("category"):
                user_cat = user["category"].lower()
                
                is_match = False
                for d_cat in detected_cats:
                    if d_cat in user_cat or user_cat in d_cat:
                        is_match = True
                        break
                        
                if is_match:
                    passed_criteria += 1
                    matched.append(f"Category matches (inferred): {user['category']}")
                else:
                    reasons.append(
                        f"Scheme appears to be targeted at categories: {', '.join(detected_cats).upper()}, you are: {user['category']}"
                    )
            else:
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
    # Uses rank-based matching instead of exact equality.
    # Hybrid check: Looks at both the structured column AND free text.
    # If the free text explicitly demands a higher degree (e.g., text says PG, but structured says School),
    # the engine enforces the higher requirement.

    # 1. Get structured rank
    scheme_edu_raw = str(scheme.get("education_level", "") or "").strip().lower()
    scheme_edu_rank = EDUCATION_RANK.get(scheme_edu_raw, 0)
    effective_req_level = scheme_edu_raw

    # 2. Infer rank from free text
    elig_text = str(scheme.get("eligibility", "") or "")
    det_text = str(scheme.get("details", "") or "")
    full_text = f"{elig_text} {det_text}".lower()
    
    highest_text_rank = 0
    highest_text_level = ""
    for pattern, req_level in _EDU_KEYWORD_GUARDS:
        if re.search(pattern, full_text, re.IGNORECASE):
            rank = EDUCATION_RANK.get(req_level, 0)
            if rank > highest_text_rank:
                highest_text_rank = rank
                highest_text_level = req_level

    # 3. Take the maximum required rank
    if highest_text_rank > scheme_edu_rank:
        scheme_edu_rank = highest_text_rank
        effective_req_level = highest_text_level

    if scheme_edu_rank > 0:
        total_criteria += 1

        if user.get("education_level"):
            user_edu_key = str(user["education_level"]).strip().lower()
            user_edu_rank = EDUCATION_RANK.get(user_edu_key, 0)

            if effective_req_level == "school":
                # School-specific schemes: strictly for school students only
                if user_edu_rank == EDUCATION_RANK["school"]:
                    passed_criteria += 1
                    matched.append("Education level matches: School")
                else:
                    reasons.append(
                        f"Scheme is only for school students; you are studying at {user['education_level'].upper()} level."
                    )
            elif user_edu_rank >= scheme_edu_rank and user_edu_rank > 0:
                # User's education is at or above what the scheme requires
                passed_criteria += 1
                matched.append(
                    f"Education level eligible: you are {user['education_level'].upper()}, "
                    f"scheme requires {effective_req_level.upper()} or above"
                )
            else:
                reasons.append(
                    f"Scheme requires {effective_req_level.upper()} level education; "
                    f"you are at {user['education_level'].upper()} level."
                )
        else:
            passed_criteria += 0.5

    # ── Course ─────────────────────────────────────
    # Part A: Structured column match (when course column is populated)
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

    # Part B: Free-text course relevance scan (when course column is null)
    # Scans eligibility + details free text using tight SCHEME_COURSE_PATTERNS
    # to detect if the scheme is restricted to specific disciplines.
    # Only activates when the scheme's structured 'course' column is empty.
    elif user.get("course"):
        eligibility_text = str(scheme.get("eligibility", "") or "").lower()
        details_text = str(scheme.get("details", "") or "").lower()
        combined_text = f"{eligibility_text} {details_text}"
        user_course = user["course"].lower()

        # Detect which discipline(s) the scheme's free text explicitly targets
        scheme_disciplines = []
        for pattern, discipline_label in SCHEME_COURSE_PATTERNS:
            if re.search(pattern, combined_text, re.IGNORECASE):
                scheme_disciplines.append(discipline_label)

        if scheme_disciplines:
            # Scheme explicitly mentions specific discipline(s) —
            # check if user's course belongs to any of them
            total_criteria += 1
            user_matches_any = False
            for pattern, discipline_label in USER_COURSE_PATTERNS:
                if re.search(pattern, user_course, re.IGNORECASE):
                    # User discipline identified — see if it's in the scheme's target set
                    if discipline_label in scheme_disciplines:
                        user_matches_any = True
                        passed_criteria += 1
                        matched.append(f"Course relevant to scheme discipline: {discipline_label}")
                    break  # Only detect user's discipline once
            if not user_matches_any:
                discipline_names = ", ".join(scheme_disciplines[:3])
                reasons.append(
                    f"Scheme is targeted at {discipline_names} students; "
                    f"your course ({user['course']}) does not match."
                )
        # If scheme text mentions NO specific discipline → open to all courses, skip check

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
    INDIAN_STATES = [
        'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
        'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
        'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
        'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana',
        'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal',
        'andaman and nicobar', 'chandigarh', 'dadra and nagar haveli', 'daman and diu',
        'delhi', 'jammu and kashmir', 'ladakh', 'lakshadweep', 'puducherry'
    ]

    eligibility_text_raw = str(scheme.get("eligibility", "") or "")
    details_text_raw = str(scheme.get("details", "") or "")
    full_text = f"{eligibility_text_raw} {details_text_raw}".lower()

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
    else:
        # Fallback: scan free text for state names if structured column is empty
        mentioned_states = [s for s in INDIAN_STATES if re.search(r'\b' + re.escape(s) + r'\b', full_text)]
        
        # We only strictly enforce text-based state matching if exactly ONE state is mentioned
        # to avoid false rejections on central schemes that list multiple states as examples.
        if len(mentioned_states) == 1:
            total_criteria += 1
            detected_state = mentioned_states[0]
            if user.get("state"):
                user_state = user["state"].lower()
                if user_state == detected_state:
                    passed_criteria += 1
                    matched.append(f"State matches (inferred): {detected_state.title()}")
                else:
                    reasons.append(
                        f"Scheme appears to be for state: {detected_state.title()}, you are from: {user['state']}"
                    )
            else:
                passed_criteria += 0.5

    # ── Marital Status ─────────────────────────────
    # Scans eligibility + details free text for marital requirements.
    # Applies to ~30 schemes (widow-specific, single girl, unmarried criteria).
    eligibility_text_raw = str(scheme.get("eligibility", "") or "")
    details_text_raw = str(scheme.get("details", "") or "")
    full_marital_text = f"{eligibility_text_raw} {details_text_raw}".lower()

    for pattern, required_status in _MARITAL_PATTERNS:
        if re.search(pattern, full_marital_text, re.IGNORECASE):
            total_criteria += 1
            user_marital = str(user.get("marital_status") or "").strip().lower()

            if not user_marital:
                # Marital status not provided — don't outright reject, give partial credit
                passed_criteria += 0.5
            elif required_status == 'widow' and user_marital == 'widow':
                passed_criteria += 1
                matched.append("Marital status matches: widow/widower requirement")
            elif required_status == 'unmarried' and user_marital in ('single', 'unmarried'):
                passed_criteria += 1
                matched.append("Marital status matches: unmarried/single requirement")
            elif required_status == 'married' and user_marital == 'married':
                passed_criteria += 1
                matched.append("Marital status matches: married requirement")
            elif required_status == 'widow' and user_marital != 'widow':
                reasons.append(
                    f"Scheme is for widows/widowers; your marital status is: {user_marital}"
                )
            elif required_status == 'unmarried' and user_marital not in ('single', 'unmarried'):
                reasons.append(
                    f"Scheme requires applicant to be unmarried/single; your status is: {user_marital}"
                )
            elif required_status == 'married' and user_marital != 'married':
                reasons.append(
                    f"Scheme requires applicant to be married; your status is: {user_marital}"
                )
            break  # Only apply the first/strongest marital requirement found

    # ── Siblings / Only Child ──────────────────────
    for pattern, requirement in _SIBLINGS_PATTERNS:
        if re.search(pattern, full_marital_text, re.IGNORECASE):
            total_criteria += 1
            user_siblings = str(user.get("siblings") or "").strip().lower()

            if not user_siblings:
                passed_criteria += 0.5  # Benefit of doubt if not provided
            elif requirement == 'only_child':
                if 'only' in user_siblings:
                    passed_criteria += 1
                    matched.append("Meets 'Only Child' requirement")
                else:
                    reasons.append(f"Scheme is for an 'Only Child'. You indicated: {user.get('siblings')}")
            elif requirement == 'max_two':
                if 'only' in user_siblings or '1 sibling' in user_siblings:
                    passed_criteria += 1
                    matched.append("Meets 'Maximum two children' requirement")
                else:
                    reasons.append(f"Scheme is for families with max 2 children. You indicated: {user.get('siblings')}")
            break

    # ── Institution Type ───────────────────────────
    for pattern, requirement in _INSTITUTION_PATTERNS:
        if re.search(pattern, full_marital_text, re.IGNORECASE):
            total_criteria += 1
            user_inst = str(user.get("institution_type") or "").strip().lower()

            if not user_inst or 'other' in user_inst:
                passed_criteria += 0.5  # Benefit of doubt if not provided or 'Other'
            elif requirement == 'gov':
                if 'gov' in user_inst or 'aided' in user_inst:
                    passed_criteria += 1
                    matched.append("Meets 'Government / Aided Institution' requirement")
                else:
                    reasons.append(f"Scheme requires studying in a Government/Aided institution. You are in a {user.get('institution_type')} institution.")
            break

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