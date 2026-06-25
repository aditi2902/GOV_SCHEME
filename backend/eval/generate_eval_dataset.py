"""
RAGAS Evaluation Step 1: Generate Evaluation Dataset

Loads the golden_dataset.json questions, runs them through the RAG pipeline
(search_schemes + chat_answer), and saves the results to eval_results.json.

Run from the backend/ directory:
    python eval/generate_eval_dataset.py
"""

import sys
import json
import os
import time
from pathlib import Path

# Allow imports from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag_agent import search_schemes, chat_answer

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
OUTPUT_PATH = Path(__file__).parent / "eval_results.json"


def generate_eval_dataset():
    """Run each golden question through the RAG pipeline and save results."""

    print(f"Loading golden dataset from {GOLDEN_DATASET_PATH} ...")
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        golden = json.load(f)

    print(f"Found {len(golden)} test questions. Running RAG pipeline...\n")

    results = []
    for i, item in enumerate(golden, start=1):
        question = item["question"]
        category = item.get("category", "unknown")
        ground_truth = item.get("ground_truth")  # May be null

        print(f"[{i:2d}/{len(golden)}] [{category}] {question[:70]}...")

        # Step 1: Retrieve context from ChromaDB
        docs = search_schemes(question, n_results=5)
        contexts = [d["content"] for d in docs]

        # Step 2: Generate answer via RAG
        answer = "ERROR: Max retries exceeded"
        for attempt in range(3):
            try:
                answer = chat_answer(question)
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"         ⚠️ Rate limit hit. Waiting 60s before retry {attempt+1}/3...")
                    time.sleep(60)
                else:
                    answer = f"ERROR: {error_str}"
                    break

        results.append({
            "question": question,
            "category": category,
            "answer": answer,
            "contexts": contexts,
            "ground_truth": ground_truth,
        })

        print(f"         ✓ {len(contexts)} contexts retrieved, answer: {len(answer)} chars")
        time.sleep(5)  # 5s delay between calls to respect the 15 RPM free tier limit

    # Save to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Eval dataset saved to {OUTPUT_PATH}")
    print(f"   Total: {len(results)} questions processed")


if __name__ == "__main__":
    generate_eval_dataset()
