"""
ChromaDB Ingestion Script
Loads scheme CSV data into ChromaDB vector store for RAG.

Run once: python ingest.py
"""

import pandas as pd
import chromadb
from config import SCHEMES_CSV, CHROMA_DIR, CHROMA_COLLECTION


def ingest_schemes():
    """Load scheme data from CSV into ChromaDB."""

    print(f"Loading schemes from {SCHEMES_CSV}...")
    df = pd.read_csv(SCHEMES_CSV)
    print(f"Loaded {len(df)} schemes")

    # Create ChromaDB client and collection
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete existing collection if it exists (fresh start)
    try:
        chroma_client.delete_collection(CHROMA_COLLECTION)
        print("Deleted existing collection")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    print("Ingesting into ChromaDB...")

    documents = []
    metadatas = []
    ids = []

    for idx, row in df.iterrows():
        # Combine relevant text fields into a single document
        parts = []

        if pd.notna(row.get("scheme_name")):
            parts.append(f"Scheme: {row['scheme_name']}")

        if pd.notna(row.get("details")):
            parts.append(f"Details: {row['details']}")

        if pd.notna(row.get("benefits")):
            parts.append(f"Benefits: {row['benefits']}")

        if pd.notna(row.get("eligibility")):
            parts.append(f"Eligibility: {row['eligibility']}")

        if pd.notna(row.get("application")):
            parts.append(f"Application Process: {row['application']}")

        if pd.notna(row.get("documents")):
            parts.append(f"Required Documents: {row['documents']}")

        doc_text = "\n\n".join(parts)

        # Skip if document is too short
        if len(doc_text) < 50:
            continue

        # Metadata for filtering
        meta = {
            "scheme_name": str(row.get("scheme_name", "")),
            "slug": str(row.get("slug", "")),
            "level": str(row.get("level", "")),
            "category": str(row.get("schemeCategory", "")),
            "benefit_type": str(row.get("benefit_type", "")),
        }

        if pd.notna(row.get("benefit_amount")):
            meta["benefit_amount"] = float(row["benefit_amount"])

        if pd.notna(row.get("income_max")):
            meta["income_max"] = float(row["income_max"])

        documents.append(doc_text)
        metadatas.append(meta)
        ids.append(f"scheme_{idx}")

    # ChromaDB has a batch limit; insert in chunks
    BATCH_SIZE = 100
    total = len(documents)

    for i in range(0, total, BATCH_SIZE):
        end = min(i + BATCH_SIZE, total)
        collection.add(
            documents=documents[i:end],
            metadatas=metadatas[i:end],
            ids=ids[i:end],
        )
        print(f"  Ingested {end}/{total} schemes")

    print(f"\nDone! {total} schemes ingested into ChromaDB.")
    print(f"Collection count: {collection.count()}")


if __name__ == "__main__":
    ingest_schemes()
