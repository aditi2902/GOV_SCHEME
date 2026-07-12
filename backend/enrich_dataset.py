"""
Dataset enrichment: fills the structured eligibility columns
(income_max, category, education_level, course, cgpa_min, state, gender,
age_min, age_max, marital_status, siblings, institution_type) by asking
Gemini to extract them from each scheme's free-text.

RESUMABLE: only rows with processed_by_ai != True are sent to Gemini. Each
successful batch is written back to the CSV immediately and its rows are
flagged processed_by_ai=True, so re-running continues where it left off —
it does NOT re-send rows that are already done.

Usage:
    python enrich_dataset.py                # process ALL unprocessed rows
    python enrich_dataset.py --limit 15     # process only the first 15 unprocessed rows (cheap test)
    python enrich_dataset.py --dry-run       # show what WOULD be sent; make no API calls
    python enrich_dataset.py --batch-size 10 # rows per Gemini call (default 15)
"""

import sys
import json
import time
import argparse
from pathlib import Path

import pandas as pd

# Insert backend directory to sys.path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import SCHEMES_CSV, GEMINI_API_KEY, GEMINI_MODEL


SYSTEM_PROMPT = """
You are an expert data extraction assistant. Your task is to analyze details and eligibility rules of multiple government schemes and extract structured eligibility criteria for each scheme.
For each scheme, you will output a JSON object with the following keys, matching our strict taxonomy:

1. "income_max": Float or null. The maximum annual family income allowed in INR.
   - Convert monthly limits to annual (e.g., "Rs. 10,000 per month" becomes 120000).
   - "Rs. 8 lakh" becomes 800000.
   - If no income limit is mentioned, use null.
2. "category": Comma-separated string of caste categories, or null if open to all categories.
   - Allowed values in list: SC, ST, OBC, General, EBC, VJNT, SBC.
   - E.g. "SC, ST" or "OBC, EBC".
   - If the text explicitly mentions "General" or "Open category" or is open to all, include "General".
3. "disability_required": Boolean (true/false). Set to true if the scheme requires applicant to have a disability (PwD/Specially-abled/handicapped).
4. "education_level": String or null. The minimum education level required.
   - Taxonomy values:
     * "School" (for school students classes 1 to 12, pre-matric, pre-board, class 10/11/12, and college entrance exam preparation like JEE/NEET coaching taken during school).
     * "ITI" (Industrial Training Institutes).
     * "Diploma" (Polytechnic/Diploma courses).
     * "UG" (Undergraduate/College/University degree courses like B.Tech, B.Sc, B.Com, B.A, B.Ed, beyond Class 12th/Graduation/Higher studies).
     * "PG" (Postgraduate/Masters/M.Tech/MBA/M.Sc).
     * "PhD" (Doctoral/Postdoctoral).
5. "course": Comma-separated string of courses or null if open to all courses/fields.
   - Taxonomy values: Engineering, Medical, Law, Pharmacy, Agriculture, Nursing / Allied Health, Architecture / Design, Computer Science, Commerce / MBA, Science, Arts / Humanities, Education / B.Ed.
6. "cgpa_min": Float or null. The minimum academic score or percentage needed (converted to a 10-point scale: e.g. 60% becomes 6.0, 7.5 CGPA remains 7.5, 85% becomes 8.5). If no limit, use null.
7. "state": String or null. The Indian state or Union Territory this scheme is restricted to (e.g. "Rajasthan", "Tripura", "Madhya Pradesh"). Use null if it is a Central scheme open to all states.
8. "gender": String or null. Restricts to gender: "Male", "Female", or null if open to all.
9. "age_min": Integer or null. Minimum age limit in years.
10. "age_max": Integer or null. Maximum age limit in years.
11. "marital_status": Comma-separated string of allowed marital statuses, or null if open to all.
    - Taxonomy values: widow, single, married, divorced (where "unmarried" maps to "single").
12. "siblings": Comma-separated string of allowed siblings/children limit, or null if open to all.
    - Taxonomy values: Only Child, 1 Sibling, 2+ Siblings (where "maximum two children" maps to "Only Child, 1 Sibling").
13. "institution_type": Comma-separated string of allowed institution types, or null if open.
    - Taxonomy values: Govt / Aided, Private.

Input format will be a list of schemes.
Output format MUST be a JSON object containing a dictionary mapping scheme slugs to their extracted structured metadata:
{
  "schemes": {
    "scheme_slug_1": {
      "income_max": 800000.0,
      "category": "SC, ST",
      "disability_required": false,
      "education_level": "UG",
      "course": "Engineering",
      "cgpa_min": 8.5,
      "state": null,
      "gender": null,
      "age_min": 18,
      "age_max": 25,
      "marital_status": "single",
      "siblings": null,
      "institution_type": "Govt / Aided"
    },
    ...
  }
}
"""


def parse_args():
    p = argparse.ArgumentParser(description="Enrich scheme dataset with Gemini.")
    p.add_argument("--limit", type=int, default=None,
                   help="Process only the first N unprocessed rows (cheap test run).")
    p.add_argument("--batch-size", type=int, default=15,
                   help="Schemes per Gemini call (default 15).")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would be sent and make NO API calls.")
    return p.parse_args()


def main():
    args = parse_args()

    # ── Loud preflight so a bad run can never look like a silent no-op ──
    print("=" * 70)
    print("ENRICH DATASET")
    print(f"  Python      : {sys.executable}")
    print(f"  CSV         : {SCHEMES_CSV}")
    print(f"  Model       : {GEMINI_MODEL}")
    print(f"  Batch size  : {args.batch_size}")
    print(f"  Limit       : {args.limit if args.limit is not None else 'ALL unprocessed'}")
    print(f"  Dry run     : {args.dry_run}")
    print("=" * 70)

    if not SCHEMES_CSV.exists():
        print(f"❌ CSV not found at {SCHEMES_CSV}. Aborting.")
        sys.exit(1)

    if not GEMINI_API_KEY and not args.dry_run:
        print("❌ GEMINI_API_KEY not found in environment / .env file. "
              "Add it to .env or run with --dry-run to preview.")
        sys.exit(1)

    df = pd.read_csv(SCHEMES_CSV)
    print(f"Loaded {len(df)} schemes.")

    # Ensure all target columns exist
    new_cols = ["income_max", "category", "disability_required", "education_level",
                "course", "cgpa_min", "state", "gender", "age_min", "age_max",
                "marital_status", "siblings", "institution_type"]
    for col in new_cols:
        if col not in df.columns:
            df[col] = None
        # Force object dtype: an all-NaN column loads as float64, and writing a
        # string (e.g. marital_status='single') into a float64 column raises.
        df[col] = df[col].astype(object)

    if "processed_by_ai" not in df.columns:
        df["processed_by_ai"] = False
    # Normalise the flag to real booleans (CSV may load it as strings)
    df["processed_by_ai"] = (
        df["processed_by_ai"].astype(str).str.strip().str.lower().isin(["true", "1"])
    )

    done = int(df["processed_by_ai"].sum())
    todo_df = df[~df["processed_by_ai"]]
    print(f"Already enriched by AI : {done} / {len(df)}")
    print(f"Remaining to process   : {len(todo_df)} / {len(df)}")
    print("(Only the 'remaining' rows are sent to Gemini — done rows are skipped. "
          "This is why a re-run targets the leftover rows, not the whole CSV.)")

    if len(todo_df) == 0:
        print("✅ Nothing to do — every row is already enriched.")
        return

    todo_indices = todo_df.index.tolist()
    if args.limit is not None:
        todo_indices = todo_indices[:args.limit]
    total_todo = len(todo_indices)
    print(f"This run will process  : {total_todo} rows")

    # ── Dry run: show the first batch payload and exit, no API calls ──
    if args.dry_run:
        preview_idx = todo_indices[:args.batch_size]
        preview = [
            {"slug": df.at[i, "slug"], "scheme_name": df.at[i, "scheme_name"]}
            for i in preview_idx
        ]
        print("\n--- DRY RUN: first batch that WOULD be sent to Gemini ---")
        print(json.dumps(preview, indent=2, ensure_ascii=False))
        print(f"\n(Would send {total_todo} rows total in "
              f"{(total_todo + args.batch_size - 1) // args.batch_size} batches of {args.batch_size}.)")
        print("No API calls were made.")
        return

    # ── Real run: initialise the same google.genai client the app uses ──
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    gen_config = types.GenerateContentConfig(
        temperature=0,
        response_mime_type="application/json",
    )

    print("\n🚀 Starting extraction pipeline using Gemini...")
    print("=" * 70)

    for i in range(0, total_todo, args.batch_size):
        batch_indices = todo_indices[i:i + args.batch_size]

        input_data = [
            {
                "slug": df.at[idx, "slug"],
                "scheme_name": df.at[idx, "scheme_name"],
                "details": str(df.at[idx, "details"] if "details" in df.columns else ""),
                "benefits": str(df.at[idx, "benefits"] if "benefits" in df.columns else ""),
                "eligibility": str(df.at[idx, "eligibility"] if "eligibility" in df.columns else ""),
            }
            for idx in batch_indices
        ]
        prompt = f"{SYSTEM_PROMPT}\n\nHere are the schemes to analyze:\n{json.dumps(input_data, indent=2, ensure_ascii=False)}"

        print(f"[{i + 1}-{min(i + args.batch_size, total_todo)}/{total_todo}] Calling Gemini... ", end="")
        sys.stdout.flush()

        retries = 5
        success = False
        while retries > 0 and not success:
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=gen_config,
                )
                extracted = json.loads(response.text)
                schemes_data = extracted.get("schemes", {})

                applied = 0
                for slug, meta in schemes_data.items():
                    hits = df.index[df["slug"] == slug].tolist()
                    if not hits:
                        continue
                    idx = hits[0]
                    for col in new_cols:
                        if col == "disability_required":
                            df.at[idx, col] = bool(meta.get("disability_required", False))
                        else:
                            df.at[idx, col] = meta.get(col)
                    df.at[idx, "processed_by_ai"] = True
                    applied += 1

                df.to_csv(SCHEMES_CSV, index=False)
                print(f"Success! Applied {applied} rows. Progress saved.")
                success = True
            except Exception as e:
                err_str = str(e)
                err_upper = err_str.upper()

                # Fatal config errors — retrying cannot help. Stop the whole run
                # immediately with a clear message instead of grinding through retries.
                fatal = (
                    "404" in err_str or "NOT_FOUND" in err_upper          # model unavailable to this key
                    or "PERMISSION_DENIED" in err_upper or "401" in err_str or "403" in err_str
                    or "API_KEY_INVALID" in err_upper or "INVALID_ARGUMENT" in err_upper
                )
                if fatal:
                    print("\n❌ Fatal error — stopping (retrying won't help):")
                    print(f"   {err_str[:300]}")
                    if "404" in err_str or "NOT_FOUND" in err_upper:
                        print(f"   The model '{GEMINI_MODEL}' is not available to this API key. "
                              "Set GEMINI_MODEL in .env to a model your key supports "
                              "(e.g. gemini-flash-latest).")
                    print(f"   Progress so far IS saved. Fix the issue and re-run to continue.")
                    sys.exit(1)

                retries -= 1
                is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_upper
                is_daily = is_quota and ("PERDAY" in err_upper or "PER DAY" in err_upper or "DAILY" in err_upper)
                if is_daily:
                    # A daily cap won't clear in 60s — no point retrying today.
                    print("\n❌ Daily free-tier quota exhausted for this key. Stopping.")
                    print("   Progress IS saved. Swap to a fresh key (or wait for the daily "
                          "reset ~midnight Pacific) and re-run to continue.")
                    sys.exit(1)
                elif is_quota:
                    print(f"Per-minute rate limit (429). Sleeping 30s... (retries left: {retries})")
                    if retries > 0:
                        time.sleep(30)
                else:
                    print(f"Failed: {err_str[:200]} (retries left: {retries})")
                    if retries > 0:
                        time.sleep(5)
                if retries == 0:
                    print("⚠️  Batch skipped after repeated errors. Re-run later to retry these rows.")

        if success:
            time.sleep(4)  # light pacing between batches

    remaining = int((~df["processed_by_ai"]).sum())
    print("\n" + "=" * 70)
    print(f"✅ Run complete. Still unprocessed: {remaining} / {len(df)}")
    if remaining:
        print("Re-run the script to continue with the remaining rows.")


if __name__ == "__main__":
    main()
