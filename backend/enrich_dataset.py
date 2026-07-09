import sys
import pandas as pd
import json
import time
from pathlib import Path

# Insert backend directory to sys.path for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import SCHEMES_CSV, GEMINI_API_KEY

def main():
    if not GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not found in environment variables. Check .env file.")
        sys.exit(1)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        print("❌ langchain-google-genai not installed. Install with: pip install langchain-google-genai")
        sys.exit(1)

    print(f"Loading dataset from {SCHEMES_CSV}...")
    df = pd.read_csv(SCHEMES_CSV)
    print(f"Loaded {len(df)} schemes.")

    # Initialize new columns if they do not exist
    new_cols = {
        "age_min": float,
        "age_max": float,
        "marital_status": str,
        "siblings": str,
        "institution_type": str
    }
    for col, c_type in new_cols.items():
        if col not in df.columns:
            df[col] = None
            df[col] = df[col].astype(object)

    if "processed_by_ai" not in df.columns:
        df["processed_by_ai"] = False
        df["processed_by_ai"] = df["processed_by_ai"].astype(bool)

    # Filter to only schemes that have not been processed yet
    todo_df = df[df["processed_by_ai"] != True]
    total_todo = len(todo_df)
    
    print(f"Total schemes needing processing: {total_todo} / {len(df)}")
    if total_todo == 0:
        print("✅ All schemes have already been processed and enriched by AI!")
        return

    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
        model_kwargs={"response_mime_type": "application/json"}
    )

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

    BATCH_SIZE = 15
    todo_indices = todo_df.index.tolist()
    
    print("\n🚀 Starting sequential extraction pipeline using Gemini...")
    print("======================================================================")

    for i in range(0, total_todo, BATCH_SIZE):
        batch_indices = todo_indices[i:i+BATCH_SIZE]
        batch = df.loc[batch_indices]
        
        # Build batch input
        input_data = []
        for _, row in batch.iterrows():
            input_data.append({
                "slug": row["slug"],
                "scheme_name": row["scheme_name"],
                "details": str(row.get("details", "")),
                "benefits": str(row.get("benefits", "")),
                "eligibility": str(row.get("eligibility", ""))
            })
            
        prompt = f"{SYSTEM_PROMPT}\n\nHere are the schemes to analyze:\n{json.dumps(input_data, indent=2)}"
        
        print(f"[{i + 1}-{min(i + BATCH_SIZE, total_todo)}/{total_todo}] Calling Gemini... ", end="")
        sys.stdout.flush()
        
        retries = 5
        success = False
        while retries > 0 and not success:
            try:
                response = llm.invoke(prompt)
                extracted = json.loads(response.content)
                schemes_data = extracted.get("schemes", {})
                
                # Apply extractions back to dataframe
                for slug, meta in schemes_data.items():
                    df_idx = df[df["slug"] == slug].index
                    if len(df_idx) > 0:
                        idx = df_idx[0]
                        df.at[idx, "income_max"] = meta.get("income_max")
                        df.at[idx, "category"] = meta.get("category")
                        df.at[idx, "disability_required"] = bool(meta.get("disability_required", False))
                        df.at[idx, "education_level"] = meta.get("education_level")
                        df.at[idx, "course"] = meta.get("course")
                        df.at[idx, "cgpa_min"] = meta.get("cgpa_min")
                        df.at[idx, "state"] = meta.get("state")
                        df.at[idx, "gender"] = meta.get("gender")
                        
                        df.at[idx, "age_min"] = meta.get("age_min")
                        df.at[idx, "age_max"] = meta.get("age_max")
                        df.at[idx, "marital_status"] = meta.get("marital_status")
                        df.at[idx, "siblings"] = meta.get("siblings")
                        df.at[idx, "institution_type"] = meta.get("institution_type")
                        df.at[idx, "processed_by_ai"] = True
                
                # Save progress to CSV
                df.to_csv(SCHEMES_CSV, index=False)
                print("Success! Progress saved.")
                success = True
            except Exception as e:
                retries -= 1
                err_str = str(e)
                # Check for rate limiting / resource exhaustion
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    print(f"Rate limited (429). Sleeping for 60 seconds to reset quota... (Retries left: {retries})")
                    time.sleep(60)
                else:
                    print(f"Failed: {err_str}. Retries left: {retries}...")
                    if retries > 0:
                        time.sleep(5)
                    else:
                        print("⚠️ Batch skipped due to persistent errors.")
        
        # Pacing of 6 seconds between requests to stay below 10 RPM (highly safe for Free Tier)
        if success:
            time.sleep(6)

    print("\n✅ Dataset enriched successfully!")

if __name__ == "__main__":
    main()
