# RAGAS Integration + Profile Agent Cleanup

Integrate the RAGAS evaluation framework to measure the quality of the RAG chatbot in `rag_agent.py`, and clean up the now-unused natural language profile extraction code.

---

## User Review Required

> [!IMPORTANT]
> **Profile agent removal scope** — The plan removes `profile_agent.py`, `test_profile.py`, the `/api/analyze` (text) endpoints, and the `/api/profile` endpoint. The form-based endpoints (`/api/analyze/form`, `/api/analyze/form/quick`) remain fully untouched. Please confirm this is correct.

> [!WARNING]
> **`/api/compare` endpoint** — Currently, if `user_text` is provided in a compare request, it calls `extract_profile()` to personalize the comparison. After removal, comparison will still work but will use an empty profile `{}` when no structured form data is passed. Is that acceptable, or should the compare endpoint accept a `UserProfileForm` instead of `user_text`?

> [!IMPORTANT]
> **Ground truth strategy** — The plan starts with **Option C (reference-free)**: only Faithfulness + Answer Relevancy (no ground truth needed). Context Precision and Context Recall are included in the script but will only produce meaningful scores once you add `ground_truth` to the golden dataset. Confirm this phased approach works for you.

---

## Open Questions

1. **How many test questions to start with?** The plan includes ~25 starter questions across 5 categories. Is that enough for your initial evaluation, or do you want more?
2. **RAGAS judge LLM** — The plan uses your existing Gemini API key (via `langchain-google-genai`) as the RAGAS evaluator. This avoids needing a separate OpenAI key. OK?

---

## Proposed Changes

### Phase 1: Clean Up Profile Agent (Production Code)

Remove the unused NLP-based profile extraction path from production.

---

#### [DELETE] [profile_agent.py](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/backend/profile_agent.py)
Delete entirely — no longer needed since the frontend uses form-based input.

#### [DELETE] [test_profile.py](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/backend/test_profile.py)
Delete entirely — tests the deleted `extract_profile()` function.

---

#### [MODIFY] [app.py](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/backend/app.py)

1. **Remove import** of `extract_profile` from `profile_agent` (line 24)
2. **Remove import** of `run_analysis` from `orchestrator` (line 21 — keep `run_analysis_with_profile`, `get_scheme_detail`, `get_stats`)
3. **Remove import** of `AnalyzeRequest` from `models` (line 13 — no longer needed)
4. **Delete endpoint** `/api/analyze` (lines 57-67) — text-based analysis
5. **Delete endpoint** `/api/analyze/quick` (lines 70-79) — text-based quick analysis
6. **Delete endpoint** `/api/profile` (lines 120-126) — profile extraction
7. **Simplify `/api/compare`** (lines 154-186) — remove the `extract_profile` call; use `profile or {}` directly when `user_text` is provided (comparison still works, just without profile personalization from NLP)

---

#### [MODIFY] [orchestrator.py](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/backend/orchestrator.py)

1. **Remove import** of `extract_profile` from `profile_agent` (line 9)
2. **Delete function** `run_analysis()` (lines 185-226) — the text-input pipeline that calls `extract_profile()`
3. Keep `run_analysis_with_profile()`, `_run_pipeline()`, `get_scheme_detail()`, `get_stats()` — all untouched

---

#### [MODIFY] [models.py](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/backend/models.py)

1. **Delete class** `AnalyzeRequest` (lines 11-20) — no longer used by any endpoint

---

#### [MODIFY] [api.js](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/frontend/src/api.js)

1. **Delete function** `analyzeProfile()` (lines 3-11) — calls removed `/api/analyze`
2. **Delete function** `analyzeQuick()` (lines 39-47) — calls removed `/api/analyze/quick`
3. Keep `analyzeForm()`, `analyzeFormQuick()`, `chatWithAI()`, `compareSchemes()`, `getSchemeDetail()`, `getStats()`

---

### Phase 2: RAGAS Evaluation Infrastructure (New Files)

All new files live in `backend/eval/` — completely separate from production code.

---

#### [NEW] backend/eval/golden_dataset.json

A hand-crafted set of ~25 test questions covering 5 categories:

| Category | Example Question | Count |
|---|---|---|
| **Factual** | "What documents are needed for PM Scholarship?" | ~5 |
| **Eligibility** | "What is the income limit for NSP OBC scholarship?" | ~5 |
| **Benefits** | "How much scholarship does PM Scholarship give per month?" | ~5 |
| **Application** | "How do I apply for the state merit scholarship?" | ~5 |
| **Comparative** | "Which scheme gives the highest benefit for engineering students?" | ~5 |

Each entry has:
```json
{
  "question": "...",
  "ground_truth": null
}
```
`ground_truth` is `null` initially (reference-free mode). Can be filled in later for Context Recall / Answer Correctness metrics.

---

#### [NEW] backend/eval/generate_eval_dataset.py

Script that:
1. Loads `golden_dataset.json`
2. For each question, calls `search_schemes(question, n_results=5)` to get retrieved contexts
3. Calls `chat_answer(question)` to get the generated answer
4. Saves a complete evaluation dataset to `backend/eval/eval_results.json` with:
   ```json
   {
     "question": "...",
     "answer": "...(generated by system)...",
     "contexts": ["...(retrieved doc 1)...", "...(retrieved doc 2)..."],
     "ground_truth": null
   }
   ```

---

#### [NEW] backend/eval/run_ragas_eval.py

Script that:
1. Loads `eval_results.json`
2. Converts to a HuggingFace `Dataset` object
3. Configures RAGAS to use **Gemini** as the judge LLM (via `langchain-google-genai`)
4. Runs these metrics:
   - **Faithfulness** — Is the answer grounded in retrieved context?
   - **Answer Relevancy** — Does the answer address the question?
   - **Context Precision** — Are retrieved docs relevant? (meaningful only with ground truth)
   - **Context Recall** — Were all needed docs retrieved? (meaningful only with ground truth)
5. Prints a score summary table
6. Saves detailed per-question scores to `backend/eval/ragas_scores.json`

---

### Phase 3: Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/Shloka%20Pol/OneDrive/Desktop/GOV_SCHEME/requirements.txt)

Add under a new `# Evaluation` section:
```
# Evaluation (RAGAS)
ragas
datasets
langchain-google-genai
```

---

## Verification Plan

### Automated Tests

```bash
# 1. Verify the backend still starts without errors after profile agent removal
cd backend
python -c "from app import app; print('App imports OK')"

# 2. Verify form-based endpoints still work
python -c "from orchestrator import run_analysis_with_profile; print('Orchestrator OK')"

# 3. Run the eval dataset generation
python eval/generate_eval_dataset.py

# 4. Run RAGAS evaluation
python eval/run_ragas_eval.py
```

### Manual Verification

1. Start the backend (`uvicorn app:app --reload`) and confirm:
   - `/api/health` returns OK
   - `/api/analyze/form` works with form data
   - `/api/chat` works with a test question
   - `/api/analyze` returns 404 (removed)
   - `/api/profile` returns 404 (removed)
2. Review RAGAS score output — Faithfulness and Answer Relevancy should be > 0.0 (indicating the pipeline ran correctly)

---

## File Summary

| Action | File | Purpose |
|---|---|---|
| DELETE | `backend/profile_agent.py` | Unused NLP profile agent |
| DELETE | `backend/test_profile.py` | Tests for deleted agent |
| MODIFY | `backend/app.py` | Remove text endpoints + profile import |
| MODIFY | `backend/orchestrator.py` | Remove `run_analysis()` + profile import |
| MODIFY | `backend/models.py` | Remove `AnalyzeRequest` model |
| MODIFY | `frontend/src/api.js` | Remove unused API functions |
| MODIFY | `requirements.txt` | Add RAGAS dependencies |
| NEW | `backend/eval/golden_dataset.json` | Test questions |
| NEW | `backend/eval/generate_eval_dataset.py` | Dataset generation script |
| NEW | `backend/eval/run_ragas_eval.py` | RAGAS evaluation runner |
