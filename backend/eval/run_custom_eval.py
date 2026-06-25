"""
Custom RAG Evaluation Script
Computes Faithfulness and Answer Relevancy metrics using Gemini 2.0/2.5 Flash
and Gemini Text Embeddings, designed to be 100% reliable under the 15 RPM free tier limit.

Bypasses the heavy Ragas library to avoid:
  - 180s timeouts caused by async queue hangs
  - Rate-limit (429) spikes from parallel requests
  - Dependency conflicts and import errors
"""

import sys
import json
import time
import math
import numpy as np
from pathlib import Path

# Allow imports from backend/ for config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GEMINI_API_KEY

EVAL_RESULTS_PATH = Path(__file__).parent / "eval_results2.json"
SCORES_OUTPUT_PATH = Path(__file__).parent / "ragas_scores.json"

# ── Prompts ───────────────────────────────────────────────────────────────

FAITHFULNESS_PROMPT = """
You are an expert judge evaluating a Question Answering system.
Your task is to evaluate the FAITHFULNESS of the generated answer based on the provided context.
Faithfulness measures whether the claims made in the answer are fully supported by the context, without any hallucination or external information.

Input:
- Context: {context}
- Question: {question}
- Answer: {answer}

Instructions:
1. Carefully read the Context and the Answer.
2. Break down the Answer into individual, distinct factual statements/claims.
3. For each statement, determine if it is directly and fully supported by the Context.
   - A statement is supported (true) only if it can be directly inferred from the Context.
   - If the statement contains or implies information not present in the Context, or contradicts the Context, it is NOT supported (false).
4. Output your analysis in JSON format with the following keys:
   - "statements": A list of objects, each containing:
     - "statement": The extracted claim/statement from the answer.
     - "supported": A boolean (true/false) indicating if it is supported by the context.
     - "reason": A brief explanation of why it is or is not supported.
   - "score": A float between 0.0 and 1.0, representing the ratio of supported statements to total statements. If there are no statements, the score should be 1.0.

Ensure your output is ONLY the raw JSON block. Do not include markdown formatting like ```json or any other text.
"""

ANSWER_RELEVANCY_PROMPT = """
You are an expert judge evaluating a Question Answering system.
Your task is to generate exactly 3 different, relevant, and specific questions that the provided Answer would be a perfect, direct, and complete response to.
Do not refer to the original question. Focus only on the content of the Answer.

Input:
- Answer: {answer}

Instructions:
1. Carefully read the Answer.
2. Generate 3 distinct questions that could be fully answered by this Answer.
3. Output your response in JSON format with the following keys:
   - "generated_questions": A list of exactly 3 strings.

Ensure your output is ONLY the raw JSON block. Do not include markdown formatting like ```json or any other text.
"""

# ── Helper Functions ──────────────────────────────────────────────────────

def cosine_similarity(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def call_with_retry(api_func, *args, max_retries=3, delay=6, **kwargs):
    """Calls an API function with retries and exponential backoff on failure."""
    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            wait_time = delay * (2 ** attempt)
            print(f"\n  ⚠️ API call failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

# ── Main Execution ────────────────────────────────────────────────────────

def main():
    # Load dependencies
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    except ImportError:
        print("❌ Missing dependency. Run: pip install langchain-google-genai numpy")
        sys.exit(1)

    if not EVAL_RESULTS_PATH.exists():
        print(f"❌ {EVAL_RESULTS_PATH} not found.")
        sys.exit(1)

    print(f"📖 Loading eval results from {EVAL_RESULTS_PATH} ...")
    with open(EVAL_RESULTS_PATH, "r", encoding="utf-8") as f:
        eval_results = json.load(f)
    
    total_questions = len(eval_results)
    print(f"Loaded {total_questions} Q&A pairs.")
    print("Initializing Gemini models in JSON mode...")

    # Initialize Gemini LLM in JSON mode
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0,
        model_kwargs={"response_mime_type": "application/json"}
    )

    # Initialize Gemini Embeddings
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=GEMINI_API_KEY
    )

    scores_out = []
    
    print("\n🚀 Starting Evaluation Loop...")
    print("Pacing: ~8 seconds per question (sequential, 100% rate-limit safe)")
    print("=" * 70)

    for idx, item in enumerate(eval_results):
        q = item["question"]
        a = item["answer"]
        contexts = item["contexts"]
        category = item.get("category", "default")
        
        print(f"\n[{idx + 1}/{total_questions}] Category: {category}")
        print(f"  Q: {q[:60]}...")
        
        # 1. Evaluate Faithfulness
        sys.stdout.write("  Evaluating Faithfulness... ")
        sys.stdout.flush()
        
        context_str = "\n\n".join(contexts)
        faith_prompt = FAITHFULNESS_PROMPT.format(
            context=context_str,
            question=q,
            answer=a
        )
        
        try:
            # Sleep 3s to stay well below 15 RPM
            time.sleep(3)
            response = call_with_retry(llm.invoke, faith_prompt)
            faith_data = json.loads(response.content)
            faithfulness_score = float(faith_data.get("score", 1.0))
            print(f"Done (Score: {faithfulness_score:.2f})")
        except Exception as e:
            print(f"FAILED: {e}")
            faithfulness_score = np.nan

        # 2. Evaluate Answer Relevancy
        sys.stdout.write("  Evaluating Answer Relevancy... ")
        sys.stdout.flush()
        
        relevancy_prompt = ANSWER_RELEVANCY_PROMPT.format(answer=a)
        
        try:
            # Sleep 3s to stay well below 15 RPM
            time.sleep(3)
            response = call_with_retry(llm.invoke, relevancy_prompt)
            relevancy_data = json.loads(response.content)
            gen_qs = relevancy_data.get("generated_questions", [])
            
            if len(gen_qs) >= 3:
                # Embed original question + the 3 generated questions in a single call!
                # Sleep 2s before embedding call
                time.sleep(2)
                vectors = call_with_retry(embeddings_model.embed_documents, [q] + gen_qs[:3])
                
                # Compute cosine similarities
                sim1 = cosine_similarity(vectors[0], vectors[1])
                sim2 = cosine_similarity(vectors[0], vectors[2])
                sim3 = cosine_similarity(vectors[0], vectors[3])
                relevancy_score = (sim1 + sim2 + sim3) / 3.0
                print(f"Done (Score: {relevancy_score:.2f})")
            else:
                print("FAILED (less than 3 questions generated)")
                relevancy_score = np.nan
        except Exception as e:
            print(f"FAILED: {e}")
            relevancy_score = np.nan

        # Save result
        scores_out.append({
            "question": q,
            "answer": a,
            "contexts": contexts,
            "category": category,
            "faithfulness": faithfulness_score,
            "answer_relevancy": relevancy_score
        })

    # ── Print Summary ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("EVALUATION COMPLETED - SUMMARY RESULTS")
    print("=" * 70)

    # Compute averages
    faith_scores = [s["faithfulness"] for s in scores_out if not math.isnan(s["faithfulness"])]
    rel_scores = [s["answer_relevancy"] for s in scores_out if not math.isnan(s["answer_relevancy"])]
    
    avg_faith = np.mean(faith_scores) if faith_scores else np.nan
    avg_rel = np.mean(rel_scores) if rel_scores else np.nan

    def print_metric_bar(name, score):
        if math.isnan(score):
            print(f"  {name:<30} NaN")
        else:
            bar = "█" * int(score * 20)
            print(f"  {name:<30} {score:.4f}  {bar}")

    print_metric_bar("faithfulness", avg_faith)
    print_metric_bar("answer_relevancy", avg_rel)
    print("=" * 70)

    # ── Save detailed per-question scores ─────────────────────────────────────
    # Replace NaN with None for JSON serialization
    def sanitize(obj):
        if isinstance(obj, float) and (math.isnan(obj) or np.isnan(obj)):
            return None
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    sanitized_scores = sanitize(scores_out)
    with open(SCORES_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sanitized_scores, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Detailed per-question scores saved to: {SCORES_OUTPUT_PATH}")

    # Per-category breakdown
    categories = set(s["category"] for s in scores_out)
    if categories and len(categories) > 1:
        print("\nPer-category breakdown:")
        print(f"  {'Category':<20} | {'Faithfulness':<12} | {'Answer Relevancy':<15}")
        print("-" * 55)
        for cat in sorted(categories):
            cat_faith = [s["faithfulness"] for s in scores_out if s["category"] == cat and not math.isnan(s["faithfulness"])]
            cat_rel = [s["answer_relevancy"] for s in scores_out if s["category"] == cat and not math.isnan(s["answer_relevancy"])]
            
            f_val = f"{np.mean(cat_faith):.4f}" if cat_faith else "NaN"
            r_val = f"{np.mean(cat_rel):.4f}" if cat_rel else "NaN"
            print(f"  {cat:<20} | {f_val:<12} | {r_val:<15}")
        print("-" * 55)

if __name__ == "__main__":
    main()
