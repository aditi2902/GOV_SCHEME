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


# Education level → typical (min_age, max_age) bounds for schemes targeting that level
_EDU_AGE_BOUNDS = {
    "school": (5, 19),
    "iti":    (14, 25),
    "diploma": (14, 25),
    "ug":     (16, 30),
    "pg":     (19, 35),
    "phd":    (21, 45),
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
    (r'\b(?:postgraduate|post-graduate|m\.?tech|m\.?e\.|mba|mca|m\.?sc|m\.?com|ll\.?m\.?|m\.?a\.?)\b|\bmaster\'?s\s+(?:degree|program|course)\b', 'pg'),
    # UG level
    (r'\b(?:undergraduate|under-graduate|b\.?tech|b\.?e\.|bba|bca|b\.?sc|b\.?com|ll\.?b\.?|b\.?a\.?|college|university|higher\s+education|higher\s+studies|beyond\s+class\s+12th|after\s+class\s+12th|graduation|under\s+graduation|under-graduation|tertiary\s+education)\b|\bbachelor\'?s\s+(?:degree|program|course)\b', 'ug'),
    # Diploma
    (r'\b(?:diploma|polytechnic)\b', 'diploma'),
    # School level
    (r'\b(?:school|matric|pre-matric|post-matric|intermediate|class\s+\d+|std\b|standard\b|grade\b|primary|secondary|high\s+school)\b', 'school')
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

# Age patterns -> extract explicit age limits from free text
_AGE_PATTERNS = [
    (r'\b(?:between|from)\s+(?:the\s+)?(?:age\s+of\s+)?(?:ages\s+of\s+)?(\d{1,2})\s*(?:years\s+)?(?:to|-|and)\s*(\d{1,2})\s*(?:years)?\b', 'both'),
    (r'\b(\d{1,2})\s*(?:to|-)\s*(\d{1,2})\s*years\b', 'both'),
    (r'not\s+(?:be\s+)?less\s+than\s+(\d{1,2}).*?not\s+(?:be\s+)?more\s+than\s+(\d{1,2})', 'both'),
    (r'age\s+(?:limit\s+)?(?:is\s+)?(\d{1,2})\s*(?:to|-|and)\s*(\d{1,2})', 'both'),
    (r'(?:below|maximum\s+age|not\s+(?:be\s+)?more\s+than|under|not\s+exceeding|upper\s+age|up\s+to)\s+(?:is\s+)?(\d{1,2})\s+years', 'max'),
    (r'age\s+(?:limit\s+)?(?:is\s+)?(\d{1,2})\s+years', 'max'),
    (r'(?:above|minimum\s+age|not\s+(?:be\s+)?less\s+than|at\s+least)\s+(?:is\s+)?(\d{1,2})\s+years', 'min'),
]

def extract_income_limit(text: str) -> float | None:
    """
    Extract annual family income limit in INR from scheme text when income_max is empty/NaN.
    Converts monthly limit to annual if monthly keyword is found.
    """
    text_clean = text.lower().replace('\xa0', ' ')
    # Scan the entire text for currency patterns
    matches = re.finditer(r'(?:rs\.?|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lacs|lac|thousand|k)?\b', text_clean)
    for m in matches:
        num_str = m.group(1).replace(',', '')
        suffix = m.group(2)
        try:
            val = float(num_str)
            if suffix in ['lakh', 'lacs', 'lac']:
                val *= 100000
            elif suffix in ['thousand', 'k']:
                val *= 1000
            
            # Check context (+/- 100 characters around the matched span)
            start_idx = max(0, m.start() - 100)
            end_idx = min(len(text_clean), m.end() + 100)
            context = text_clean[start_idx:end_idx]
            
            if any(kw in context for kw in ['income', 'salary', 'parental', 'family', 'household', 'earning']):
                # Detect monthly limits e.g. "per month", "p.m.", "pm"
                is_monthly = any(m_kw in context for m_kw in ['month', 'p.m', 'pm', 'monthly'])
                if is_monthly and val < 50000:
                    val *= 12
                    
                # Reasonable annual income limit bounds
                if 10000 <= val <= 2500000:
                    return val
        except ValueError:
            continue
    return None


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
    mentioned_states = []
    is_state_restricted = False

    # Clean and extract text once
    eligibility_text_raw = str(scheme.get("eligibility", "") or "")
    details_text_raw = str(scheme.get("details", "") or "")
    full_text = f"{eligibility_text_raw} {details_text_raw}".lower().replace('&', 'and')

    # ── Foreign-Nationals-Only Check ───────────────
    # Some schemes exist to bring foreign students/teachers TO India (e.g. "JRF/RA
    # for Foreign Nationals"). Users of this platform are Indian residents, so such
    # schemes are never applicable. Only trigger when the target group is
    # exclusively foreigners — schemes that merely also admit foreign students
    # (e.g. "foreign students are exempted from the written test") must not match.
    scheme_name_lower = str(scheme.get("scheme_name", "") or "").lower()
    foreigners_only = (
        re.search(r'\bfor\s+foreign\s+(?:nationals?|students?|citizens?)\b', scheme_name_lower)
        or re.search(
            r'target\s+group\s*:?[^.]{0,120}\b(?:from\s+developing\s+countries|foreign\s+nationals?)\b',
            full_text
        )
    )
    if foreigners_only:
        reasons.append("Scheme is exclusively for foreign nationals (non-Indian applicants).")

    # ── Age Check ─────────────────────────────────
    user_age = user.get("age")
    explicit_min = None
    explicit_max = None
    
    # Check new structured columns first
    if pd.notna(scheme.get("age_min")):
        explicit_min = int(scheme["age_min"])
    if pd.notna(scheme.get("age_max")):
        explicit_max = int(scheme["age_max"])

    if explicit_min is None and explicit_max is None:
        for pattern, p_type in _AGE_PATTERNS:
            m = re.search(pattern, full_text, re.IGNORECASE)
            if m:
                if p_type == 'both' and len(m.groups()) >= 2:
                    if explicit_min is None: explicit_min = int(m.group(1))
                    if explicit_max is None: explicit_max = int(m.group(2))
                elif p_type == 'max' and len(m.groups()) >= 1:
                    if explicit_max is None: explicit_max = int(m.group(1))
                elif p_type == 'min' and len(m.groups()) >= 1:
                    if explicit_min is None: explicit_min = int(m.group(1))

    # Explicit Internship check for age
    if 'internship' in str(scheme.get("benefit_type", "")).lower() or 'internship' in str(scheme.get("scheme_name", "")).lower():
        if explicit_min is None or explicit_min < 18:
            explicit_min = 18

    if explicit_min is not None or explicit_max is not None:
        total_criteria += 1
        if user_age is not None:
            if explicit_min and user_age < explicit_min:
                reasons.append(f"Scheme minimum age is {explicit_min}, you are {user_age}.")
            elif explicit_max and user_age > explicit_max:
                reasons.append(f"Scheme maximum age is {explicit_max}, you are {user_age}.")
            else:
                passed_criteria += 1
                matched.append(f"Age {user_age} satisfies scheme age limits.")
        else:
            # Age not provided, give partial credit
            passed_criteria += 0.5
    else:
        # Fallback: Use scheme's education_level to infer realistic age bounds.
        scheme_edu_raw = scheme.get("education_level")
        if pd.notna(scheme_edu_raw) and user_age is not None:
            scheme_edu_key = str(scheme_edu_raw).strip().lower()
            bounds = _EDU_AGE_BOUNDS.get(scheme_edu_key)
            if bounds:
                min_cap, max_cap = bounds
                total_criteria += 1
                if user_age > max_cap:
                    reasons.append(
                        f"Age {user_age} is too high for a {scheme_edu_raw}-level scheme "
                        f"(typically for students up to {max_cap} years old)"
                    )
                elif user_age < min_cap:
                    reasons.append(
                        f"Age {user_age} is too young for a {scheme_edu_raw}-level scheme "
                        f"(typically for students at least {min_cap} years old)"
                    )
                else:
                    passed_criteria += 1
                    matched.append(f"Age {user_age} falls within expected age range for {scheme_edu_raw} level.")

    # ── Income Check ───────────────────────────────
    # First check structured column, then fall back to text extraction
    income_limit = None
    if pd.notna(scheme.get("income_max")):
        income_limit = float(scheme["income_max"])
    else:
        income_limit = extract_income_limit(full_text)

    if income_limit is not None:
        total_criteria += 1
        user_income = user.get("income")
        if user_income is not None:
            if user_income <= income_limit:
                passed_criteria += 1
                matched.append(
                    f"Income ₹{user_income:,.0f} within limit ₹{income_limit:,.0f}"
                )
            else:
                reasons.append(
                    f"Income ₹{user_income:,.0f} exceeds limit ₹{income_limit:,.0f}"
                )
        else:
            passed_criteria += 0.5

    # ── Gender Check ───────────────────────────────
    # Structured check, then text check fallback
    gender_req = None
    if pd.notna(scheme.get("gender")):
        gender_req = str(scheme["gender"]).strip().lower()
    else:
        # Check if text mentions restricting to a specific gender.
        # If BOTH genders are mentioned (e.g. "35 years for male candidates and
        # 40 years for female candidates"), the scheme is open to all.
        female_mentioned = bool(re.search(r'\bonly\s+girls?\b|\bfor\s+girls?\b|\bgirl\s+student\b|\bwomen\b|\bfemale\b', full_text, re.IGNORECASE))
        male_mentioned = bool(re.search(r'\bonly\s+boys?\b|\bfor\s+boys?\b|\bmale\b', full_text, re.IGNORECASE))
        if re.search(r'\b(?:transgender|trans\s+person)\b', full_text, re.IGNORECASE):
            gender_req = 'transgender'
        elif female_mentioned and not male_mentioned:
            gender_req = 'female'
        elif male_mentioned and not female_mentioned:
            gender_req = 'male'

    if gender_req:
        total_criteria += 1
        user_gender = user.get("gender")
        if user_gender:
            if user_gender.lower() == gender_req:
                passed_criteria += 1
                matched.append(f"Gender matches: {gender_req}")
            else:
                reasons.append(
                    f"Scheme is restricted to gender: {gender_req}, you are: {user_gender}"
                )
        else:
            passed_criteria += 0.5

    # ── Category / Caste Check ─────────────────────
    # Collapse dotted acronyms so "S.C." / "V.J.N.T." read as "sc" / "vjnt".
    def _collapse_acronyms(t):
        return re.sub(r'\b(?:[a-z]\.){2,}', lambda m: m.group(0).replace('.', ''), t)
    cat_text = _collapse_acronyms(full_text)
    cat_name = _collapse_acronyms(scheme_name_lower)

    # Detection patterns include acronyms AND common spelled-out forms.
    _CATEGORY_PATTERNS = {
        # (?<!\.) stops bare "sc"/"st" from matching inside degrees like "M.Sc"/"B.St"
        r'(?<!\.)\b(?:sc|scheduled\s+caste)\b': 'sc',
        r'(?<!\.)\b(?:st|scheduled\s+tribe|tribal)\b': 'st',
        r'\b(?:obc|other\s+backward\s+class(?:es)?)\b': 'obc',
        r'\b(?:ebc|sebc|economically\s+backward\s+class(?:es)?)\b': 'ebc',
        r'\b(?:vjnt|sbc|vimukta|nomadic\s+trib|denotified|special\s+backward\s+class(?:es)?)\b': 'vjnt/sbc',
    }

    # Check structured category first, fallback to text matching
    scheme_cats = []
    category_from_structured = False
    if pd.notna(scheme.get("category")):
        scheme_cats = [
            c.strip().lower()
            for c in str(scheme["category"]).split(",")
        ]
        category_from_structured = True
    else:
        for pattern, cat_label in _CATEGORY_PATTERNS.items():
            if re.search(pattern, cat_text, re.IGNORECASE):
                scheme_cats.append(cat_label)

    # Check if text explicitly mentions "general" or "open"
    has_general_mention = bool(re.search(r'\b(?:general|open|unreserved|all\s+categories)\b', full_text, re.IGNORECASE))
    general_allowed = ('general' in scheme_cats) or has_general_mention

    # Strong exclusivity language — only trust a text-derived category as a true
    # restriction when the scheme is genuinely *reserved* for it. A bare mention
    # of "SC" (e.g. "SC students get an extra stipend") is NOT an exclusion, and
    # previously caused General/other users to be wrongly rejected. But "should
    # belong to <category>" IS a membership requirement, so it counts.
    _RESERVED_TOKEN = (r'(?:sc|st|obc|ebc|sebc|vjnt|sbc|scheduled\s+caste|scheduled\s+tribe'
                       r'|backward\s+class(?:es)?|vimukta|nomadic\s+trib|denotified)')
    exclusive_reserved = bool(re.search(
        rf'\b(?:only|exclusively|solely|reserved)\b[^.]{{0,50}}\b{_RESERVED_TOKEN}\b'
        rf'|\b(?:should|must)?\s*belong(?:ing|s)?\s+to\b[^.]{{0,40}}\b{_RESERVED_TOKEN}\b'
        rf'|\bfor\s+{_RESERVED_TOKEN}\s*/?\s*{_RESERVED_TOKEN}?\s+(?:students?|candidates?|category|girls?|boys?|children)\b',
        cat_text, re.IGNORECASE
    ))

    # A reserved category named in the SCHEME TITLE (e.g. "...for VJNT Students",
    # "SC/ST Scholarship") is itself a strong exclusion signal — such schemes exist
    # specifically for that category, so a mismatched user should be filtered out.
    _cat_name_tokens = []
    for c in scheme_cats:
        _cat_name_tokens.extend(t for t in c.split('/') if t and t != 'general')
    name_targets_reserved = any(
        re.search(rf'\b{re.escape(tok)}\b', cat_name) for tok in _cat_name_tokens
    )

    # Enforce the category as a hard filter when it's authoritative (structured
    # column), the text is explicitly exclusive, or the title names the category.
    category_is_restriction = bool(scheme_cats) and (
        category_from_structured or exclusive_reserved or name_targets_reserved
    )

    if scheme_cats:
        user_cat = user.get("category")
        if user_cat:
            user_cat_lower = user_cat.lower()
            if user_cat_lower == 'general':
                if general_allowed:
                    matched.append("Category matches: General (open category)")
                elif category_is_restriction:
                    reasons.append(
                        f"Scheme is restricted to reserved categories ({', '.join(scheme_cats).upper()}); you are General."
                    )
                else:
                    matched.append(
                        "Category: reserved categories only mentioned in passing; General treated as eligible"
                    )
            else:
                is_match = False
                for s_cat in scheme_cats:
                    if s_cat in user_cat_lower or user_cat_lower in s_cat:
                        is_match = True
                        break
                if is_match:
                    matched.append(f"Category matches: {user_cat}")
                elif category_is_restriction:
                    reasons.append(
                        f"Scheme requires category: {', '.join(scheme_cats).upper()}, you are: {user_cat}"
                    )
                else:
                    matched.append(
                        "Category: reserved categories only mentioned in passing; treated as eligible"
                    )

    # ── Community Check ────────────────────────────
    # Look for specific communities in text
    community_reqs = []
    _COMMUNITIES = ['hindu', 'muslim', 'christian', 'sikh', 'buddhist', 'jain', 'parsi']
    for comm in _COMMUNITIES:
        if re.search(rf'\b{comm}\b', full_text, re.IGNORECASE):
            community_reqs.append(comm)
            
    if community_reqs:
        total_criteria += 1
        user_comm = user.get("community")
        if user_comm:
            user_comm_lower = user_comm.lower()
            if user_comm_lower in community_reqs:
                passed_criteria += 1
                matched.append(f"Community matches: {user_comm}")
            else:
                reasons.append(f"Scheme is for {', '.join(community_reqs).title()} community; you are {user_comm}.")
        else:
            passed_criteria += 0.5

    # ── Residence Type Check ───────────────────────
    residence_reqs = []
    if re.search(r'\brural\b', full_text, re.IGNORECASE):
        residence_reqs.append('rural')
    if re.search(r'\burban\b|\bcity\b', full_text, re.IGNORECASE):
        residence_reqs.append('urban')
        
    # If both are mentioned, it's likely open to both, so we only restrict if exactly one is required
    if len(residence_reqs) == 1:
        req = residence_reqs[0]
        total_criteria += 1
        user_res = user.get("residence_type")
        if user_res:
            if user_res.lower() == req:
                passed_criteria += 1
                matched.append(f"Residence matches: {req.title()}")
            else:
                reasons.append(f"Scheme is for {req.title()} areas; you are from {user_res} area.")
        else:
            passed_criteria += 0.5

    # ── Disability Check ───────────────────────────
    # Structured check, then text fallback
    disability_required = False
    if scheme.get("disability_required"):
        disability_required = True
    elif re.search(r'\b(?:disabled|disability|specially-abled|specially\s+abled|handicapped|divyang|pwd|person\s+with\s+disabilit\w+)\b', full_text, re.IGNORECASE):
        disability_required = True

    if disability_required:
        total_criteria += 1
        if user.get("disability"):
            passed_criteria += 1
            matched.append("Disability requirement met")
        else:
            reasons.append("Scheme requires disability status")

    # ── Education Level / Study Degree Check ───────
    # We now strictly check if the user's education level is explicitly allowed.
    scheme_edu_raw = str(scheme.get("education_level", "") or "").strip().lower()
    explicit_levels = [s.strip() for s in scheme_edu_raw.split(",") if s.strip()]
    allowed_ranks = {EDUCATION_RANK.get(lvl, 0) for lvl in explicit_levels if EDUCATION_RANK.get(lvl, 0) > 0}

    # Infer ranks from free text if column is empty
    inferred_ranks = set()
    highest_text_level = ""
    for pattern, req_level in _EDU_KEYWORD_GUARDS:
        if re.search(pattern, full_text, re.IGNORECASE):
            rank = EDUCATION_RANK.get(req_level, 0)
            inferred_ranks.add(rank)
            highest_text_level = req_level

    if allowed_ranks:
        target_ranks = allowed_ranks
        effective_req_level = explicit_levels[0]
        # Guard against mislabeled structured data: if the column says the scheme
        # is for School/ITI/Diploma students but the free text clearly requires a
        # Master's/PhD and never mentions school-level study, trust the text.
        if (
            inferred_ranks
            and max(inferred_ranks) >= EDUCATION_RANK["pg"]
            and max(allowed_ranks) < EDUCATION_RANK["ug"]
            and EDUCATION_RANK["school"] not in inferred_ranks
        ):
            highest_rank = max(inferred_ranks)
            target_ranks = {highest_rank}
            effective_req_level = [k for k, v in EDUCATION_RANK.items() if v == highest_rank][0]
    else:
        # If the inferred text mentions PG or PhD, it is very likely a Master's or Research scheme.
        # We enforce strict checking by only retaining the highest rank.
        # This prevents UG students from matching just because the text mentioned "undergraduate".
        if inferred_ranks and max(inferred_ranks) >= EDUCATION_RANK["pg"]:
            highest_rank = max(inferred_ranks)
            target_ranks = {highest_rank}
            effective_req_level = [k for k, v in EDUCATION_RANK.items() if v == highest_rank][0]
        else:
            target_ranks = inferred_ranks
            effective_req_level = highest_text_level

    # Infer specific school levels and exact class ranges
    min_class_req = None
    max_class_req = None
    
    if EDUCATION_RANK.get("school", 0) in target_ranks:
        # First check keywords
        if re.search(r'\bprimary\b', full_text, re.IGNORECASE):
            min_class_req = 1
            max_class_req = 5
        if re.search(r'\bupper\s+primary\b|\bmiddle\s+school\b', full_text, re.IGNORECASE):
            min_class_req = 6
            max_class_req = 8
        if re.search(r'\bsecondary\b|\bhigh\s+school\b', full_text, re.IGNORECASE):
            min_class_req = 9
            max_class_req = 10
        if re.search(r'\bhigher\s+secondary\b|\bsenior\s+secondary\b|\bintermediate\b|\b10\+2\b', full_text, re.IGNORECASE):
            min_class_req = 11
            max_class_req = 12

        # Then look for explicit class ranges like "class 1 to 10" or "class ix to xii"
        def parse_class_val(val_str):
            if not val_str: return None
            val = val_str.lower().strip()
            roman_map = {'i':1, 'ii':2, 'iii':3, 'iv':4, 'v':5, 'vi':6, 'vii':7, 'viii':8, 'ix':9, 'x':10, 'xi':11, 'xii':12}
            if val in roman_map: return roman_map[val]
            try: return int(val)
            except: return None

        class_regex_group = r'([1-9]|1[0-2]|xii|xi|x|ix|viii|vii|vi|iv|v|iii|ii|i)'
        # Ordinal-before-word form common in Indian scheme texts: "12th standard", "9th to 12th class"
        ordinal_group = r'([1-9]|1[0-2])(?:st|nd|rd|th)'
        class_patterns = [
            rf'\b(?:class|std\.?|standard|grade)s?\s+{class_regex_group}\s*(?:to|-|and)\s*{class_regex_group}\b',
            rf'\b(?:from\s+)?(?:class|std\.?|standard|grade)s?\s+{class_regex_group}\s+to\s+{class_regex_group}\b',
            rf'\b{ordinal_group}?\s*(?:to|-|or|and)\s*{ordinal_group}\s+(?:class|std\.?|standard|grade)s?\b'
        ]
        
        found_range = False
        
        # Check for "Class X and above / X+"
        above_pattern = rf'\b(?:class|std\.?|standard|grade)s?\s+{class_regex_group}\s*(?:and\s+above|or\s+above|and\s+higher|or\s+higher|onwards?|\+)\b'
        m_above = re.search(above_pattern, full_text, re.IGNORECASE)
        if m_above:
            c1 = parse_class_val(m_above.group(1))
            if c1:
                min_class_req = c1
                max_class_req = 12
                found_range = True
        
        if not found_range:
            for p in class_patterns:
                m = re.search(p, full_text, re.IGNORECASE)
                if m:
                    c1, c2 = parse_class_val(m.group(1)), parse_class_val(m.group(2))
                    if c1 and c2:
                        min_class_req = min(c1, c2)
                        max_class_req = max(c1, c2)
                        found_range = True
                        break
                    
        # If no range found, try to find single classes mentioned
        if not found_range:
            single_classes = []
            for m in re.finditer(rf'\b(?:class|std\.?|standard|grade)s?\s+{class_regex_group}\b', full_text, re.IGNORECASE):
                val = parse_class_val(m.group(1))
                if val: single_classes.append(val)
            # Ordinal-before-word form: "12th standard", "10th class"
            for m in re.finditer(rf'\b{ordinal_group}\s+(?:class|std\.?|standard|grade)s?\b', full_text, re.IGNORECASE):
                val = parse_class_val(m.group(1))
                if val: single_classes.append(val)
            if single_classes:
                min_class_req = min(single_classes)
                max_class_req = max(single_classes)

    if target_ranks:
        total_criteria += 1

        if user.get("education_level"):
            user_edu_key = str(user["education_level"]).strip().lower()
            user_edu_rank = EDUCATION_RANK.get(user_edu_key, 0)

            if user_edu_rank == EDUCATION_RANK.get("school", 0) and EDUCATION_RANK.get("school", 0) in target_ranks:
                # School-specific schemes: strictly for school students only
                if min_class_req is not None and max_class_req is not None:
                    if user.get("year_of_study"):
                        yos = int(user["year_of_study"])
                        if min_class_req <= yos <= max_class_req:
                            passed_criteria += 1
                            matched.append(f"Education level matches: Class {yos} is within required range ({min_class_req}-{max_class_req})")
                        else:
                            reasons.append(
                                f"Scheme is for class {min_class_req} to {max_class_req}; you are in Class {yos}."
                            )
                    else:
                        # Verify via age if year of study is missing
                        if user_age:
                            min_expected_age = min_class_req + 4
                            max_expected_age = max_class_req + 7
                            if min_expected_age <= user_age <= max_expected_age:
                                passed_criteria += 1
                                matched.append(f"Age {user_age} is appropriate for required classes ({min_class_req}-{max_class_req})")
                            else:
                                reasons.append(
                                    f"Age {user_age} is outside typical range ({min_expected_age}-{max_expected_age}) for required classes ({min_class_req}-{max_class_req})."
                                )
                        else:
                            passed_criteria += 0.5
                            matched.append(f"Education level matches: Scheme is for class {min_class_req}-{max_class_req}")
                else:
                    passed_criteria += 1
                    matched.append("Education level matches: School")
            elif user_edu_rank in target_ranks and user_edu_rank > 0:
                # User's education matches one of the allowed levels
                passed_criteria += 1
                matched.append(
                    f"Education level eligible: you are pursuing {user['education_level'].upper()}, "
                    f"which matches the scheme's allowed levels."
                )
            else:
                allowed_names = [name.upper() for name, rank in EDUCATION_RANK.items() if rank in target_ranks]
                reasons.append(
                    f"Scheme is for {', '.join(allowed_names)} students; "
                    f"you are currently pursuing {user['education_level'].upper()}."
                )
        else:
            passed_criteria += 0.5

    # ── Course Check ───────────────────────────────
    # Structured check AND text fallback
    user_course = user.get("course", "")
    course_matched = False
    
    # 1. Try structured check
    if pd.notna(scheme.get("course")):
        scheme_course = str(scheme["course"]).strip().lower()
        if user_course:
            user_course_lower = user_course.lower()
            if (
                user_course_lower in scheme_course
                or scheme_course in user_course_lower
                or user_course_lower == scheme_course
            ):
                course_matched = True
                matched.append(f"Course matches (structured): {scheme['course']}")

    # 2. Try text-based matching if structured match failed or was empty
    if not course_matched and user_course:
        user_course_lower = user_course.lower()
        scheme_disciplines = []
        for pattern, discipline_label in SCHEME_COURSE_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                scheme_disciplines.append(discipline_label)

        if scheme_disciplines:
            user_matches_any = False
            for pattern, discipline_label in USER_COURSE_PATTERNS:
                if re.search(pattern, user_course_lower, re.IGNORECASE):
                    if discipline_label in scheme_disciplines:
                        user_matches_any = True
                        break
            if user_matches_any:
                course_matched = True
                matched.append(f"Course matches (text-inferred): {', '.join(scheme_disciplines)}")
            else:
                total_criteria += 1
                discipline_names = ", ".join(scheme_disciplines[:3])
                reasons.append(
                    f"Scheme is targeted at {discipline_names} students; "
                    f"your course ({user_course}) does not match."
                )
        elif pd.notna(scheme.get("course")):
            # Structured course exists but did not match, and no disciplines found in text
            total_criteria += 1
            reasons.append(
                f"Scheme requires course: {scheme['course']}, you study: {user_course}"
            )

    # ── CGPA Check ─────────────────────────────────
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

    # ── State Check ────────────────────────────────
    # Check structured column, fallback to text matching
    scheme_state = None
    if pd.notna(scheme.get("state")):
        scheme_state = str(scheme["state"]).strip().lower()

    if scheme_state:
        total_criteria += 1
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
        # Fallback state matching from text
        INDIAN_STATES = [
            'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
            'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
            'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
            'nagaland', 'odisha', 'orissa', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 'telangana',
            'tripura', 'uttar pradesh', 'uttarakhand', 'uttaranchal', 'west bengal',
            'andaman and nicobar', 'chandigarh', 'dadra and nagar haveli', 'daman and diu',
            'delhi', 'jammu and kashmir', 'ladakh', 'lakshadweep', 'puducherry'
        ]
        
        mentioned_states = [s for s in INDIAN_STATES if re.search(r'\b' + re.escape(s) + r'\b', full_text)]
        residency_restriction = bool(re.search(
            r'\b(?:resident|domicile|native|origin|inhabitants|belong to|government of|govt\.? of)\b', 
            full_text, 
            re.IGNORECASE
        ))
        is_state_restricted = (scheme.get("level") == "State") or residency_restriction

        if mentioned_states and is_state_restricted:
            total_criteria += 1
            if user.get("state"):
                user_state = user["state"].lower()
                normalized_user_state = 'odisha' if user_state == 'orissa' else ('uttarakhand' if user_state == 'uttaranchal' else user_state)
                
                is_match = False
                for m_state in mentioned_states:
                    norm_m_state = 'odisha' if m_state == 'orissa' else ('uttarakhand' if m_state == 'uttaranchal' else m_state)
                    if normalized_user_state == norm_m_state:
                        is_match = True
                        break
                
                if is_match:
                    passed_criteria += 1
                    matched.append(f"State matches (inferred): {user['state']}")
                else:
                    reasons.append(
                        f"Scheme appears to be restricted to: {', '.join(mentioned_states).title()}, you are from: {user['state']}"
                    )
            else:
                passed_criteria += 0.5

    # ── Marital Status Check ───────────────────────
    # Check structured column first, then text fallback
    allowed_statuses = set()
    has_marital_requirement = False
    
    if pd.notna(scheme.get("marital_status")):
        allowed_raw = str(scheme["marital_status"]).strip().lower()
        allowed_statuses = {s.strip() for s in allowed_raw.split(",") if s.strip()}
        if allowed_statuses:
            has_marital_requirement = True
            
    if not has_marital_requirement:
        # Check for widow
        if re.search(r'\bwidows?\b|\bwidowers?\b', full_text, re.IGNORECASE):
            allowed_statuses.add('widow')
            has_marital_requirement = True
            
        # Check for divorced/abandoned
        if re.search(r'\b(?:divorced|abandoned|deserted|separated|talaq|single\s+mothers?)\b', full_text, re.IGNORECASE):
            allowed_statuses.add('divorced')
            has_marital_requirement = True
            
        # Check for unmarried/single
        if re.search(r'\b(?:unmarried|single\s+girls?|should\s+not\s+(?:be\s+)?married|not\s+(?:be\s+)?married)\b', full_text, re.IGNORECASE):
            allowed_statuses.add('single')
            allowed_statuses.add('unmarried')
            has_marital_requirement = True
            
        # Check for married (ensure it's not "unmarried" or part of "not married")
        if re.search(r'\bmarried\b(?!\s+(?:and|or)\s+unmarried)(?!\s+and\s+abandoned)', full_text, re.IGNORECASE):
            if not re.search(r'\b(?:not|should\s+not\s+be)\s+married\b', full_text, re.IGNORECASE):
                allowed_statuses.add('married')
                has_marital_requirement = True

    if has_marital_requirement:
        total_criteria += 1
        user_marital = str(user.get("marital_status") or "").strip().lower()

        if not user_marital:
            passed_criteria += 0.5
        else:
            is_match = False
            if user_marital in allowed_statuses:
                is_match = True
            elif user_marital == 'unmarried' and 'single' in allowed_statuses:
                is_match = True
            elif user_marital == 'single' and 'unmarried' in allowed_statuses:
                is_match = True
                
            if is_match:
                passed_criteria += 1
                matched.append(f"Marital status matches: {user['marital_status']}")
            else:
                allowed_str = "/".join(sorted(list(allowed_statuses)))
                reasons.append(
                    f"Scheme requires marital status: {allowed_str.upper()}; your status is: {user_marital}"
                )

    # ── Siblings / Only Child Check ────────────────
    only_child_required = False
    max_two_required = False
    has_sibling_requirement = False
    
    if pd.notna(scheme.get("siblings")):
        allowed_raw = str(scheme["siblings"]).strip().lower()
        allowed_sibs = {s.strip() for s in allowed_raw.split(",") if s.strip()}
        if allowed_sibs:
            has_sibling_requirement = True
            if "only child" in allowed_sibs and "1 sibling" not in allowed_sibs and "2+ siblings" not in allowed_sibs:
                only_child_required = True
            elif ("only child" in allowed_sibs or "1 sibling" in allowed_sibs) and "2+ siblings" not in allowed_sibs:
                max_two_required = True

    if not has_sibling_requirement:
        only_child_required = bool(re.search(r'\bonly\s+(?:girl\s+)?child\b|\bsingle\s+(?:girl\s+)?child\b', full_text, re.IGNORECASE))
        max_two_required = bool(re.search(r'\b(?:two|2)\s+(?:children|daughters|sons)\b|\bmax(?:imum)?\s+(?:two|2)\s+children\b', full_text, re.IGNORECASE))
        has_sibling_requirement = only_child_required or max_two_required

    if has_sibling_requirement:
        total_criteria += 1
        user_siblings = str(user.get("siblings") or "").strip().lower()

        if not user_siblings:
            passed_criteria += 0.5
        else:
            if only_child_required and not max_two_required:
                if 'only' in user_siblings:
                    passed_criteria += 1
                    matched.append("Meets 'Only Child' requirement")
                else:
                    reasons.append(f"Scheme is for an 'Only Child'. You indicated: {user.get('siblings')}")
            else:
                if 'only' in user_siblings or '1 sibling' in user_siblings:
                    passed_criteria += 1
                    matched.append("Meets 'Maximum two children' requirement")
                else:
                    reasons.append(f"Scheme is for families with max 2 children. You indicated: {user.get('siblings')}")

    # ── Institution Type Check ─────────────────────
    gov_required = False
    has_inst_requirement = False
    
    if pd.notna(scheme.get("institution_type")):
        allowed_raw = str(scheme["institution_type"]).strip().lower()
        allowed_insts = {i.strip() for i in allowed_raw.split(",") if i.strip()}
        if allowed_insts:
            has_inst_requirement = True
            if "govt / aided" in allowed_insts and "private" not in allowed_insts:
                gov_required = True

    if not has_inst_requirement:
        for pattern, requirement in _INSTITUTION_PATTERNS:
            if re.search(pattern, full_text, re.IGNORECASE):
                has_inst_requirement = True
                if requirement == 'gov':
                    gov_required = True
                break

    if has_inst_requirement:
        total_criteria += 1
        user_inst = str(user.get("institution_type") or "").strip().lower()

        if not user_inst or 'other' in user_inst:
            passed_criteria += 0.5
        elif gov_required:
            if 'gov' in user_inst or 'aided' in user_inst:
                passed_criteria += 1
                matched.append("Meets 'Government / Aided Institution' requirement")
            else:
                reasons.append(f"Scheme requires studying in a Government/Aided institution. You are in a {user.get('institution_type')} institution.")
        else:
            passed_criteria += 1
            matched.append("Meets institution type requirement")

    # ── Calculate Score based on all 12 criteria ───
    # We define the 12 core criteria dimensions
    dimensions = [
        ("age", pd.notna(scheme.get("age_min")) or pd.notna(scheme.get("age_max")) or (explicit_min is not None or explicit_max is not None), user.get("age")),
        ("income", pd.notna(scheme.get("income_max")) or income_limit is not None, user.get("income")),
        ("gender", pd.notna(scheme.get("gender")) or gender_req is not None, user.get("gender")),
        ("category", category_is_restriction, user.get("category")),
        ("education_level", pd.notna(scheme.get("education_level")) or effective_req_level != "", user.get("education_level")),
        ("course", pd.notna(scheme.get("course")) or course_matched, user.get("course")),
        ("cgpa", pd.notna(scheme.get("cgpa_min")), user.get("cgpa")),
        ("state", pd.notna(scheme.get("state")) or scheme_state is not None or (bool(mentioned_states) and is_state_restricted), user.get("state")),
        ("marital_status", has_marital_requirement, user.get("marital_status")),
        ("siblings", has_sibling_requirement, user.get("siblings")),
        ("institution_type", has_inst_requirement, user.get("institution_type")),
        ("disability", disability_required, user.get("disability"))
    ]

    # Score is normalized over the criteria the scheme actually restricts
    # (its "applicable" criteria), NOT all 12. Otherwise a perfect match on a
    # scheme that only restricts a few fields could never approach 100%, which
    # made downstream thresholds (e.g. readiness_score's >=90 cutoff) unreachable.
    applicable_weight = 0.0
    applicable_count = 0
    for dim_name, is_restricted, user_val in dimensions:
        if is_restricted:
            applicable_count += 1
            if user_val is None or user_val == "" or user_val is False:
                # User did not provide info, gets partial credit (0.5)
                applicable_weight += 0.5
            else:
                # User matched restriction (since scheme is eligible)
                applicable_weight += 1.0

    if applicable_count > 0:
        match_score = round((applicable_weight / applicable_count) * 100, 1)
    else:
        # Scheme restricts nothing (open to all) — an eligible user matches fully.
        match_score = 100.0

    eligible = len(reasons) == 0

    return {
        "eligible": eligible,
        "match_score": match_score,
        "rejection_reasons": reasons,
        "matched_criteria": matched,
    }