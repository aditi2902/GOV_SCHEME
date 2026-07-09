"""
Agent 3: Scheme Discovery / RAG Agent
Uses ChromaDB for semantic search over scheme data.
Powers the chat Q&A and scheme discovery features.
"""

import chromadb
import json
from google import genai
from chromadb.utils import embedding_functions
from config import GEMINI_API_KEY, GEMINI_MODEL, CHROMA_DIR, CHROMA_COLLECTION
from orchestrator import run_analysis_with_profile

client = genai.Client(api_key=GEMINI_API_KEY)

# Initialize globally so we don't reload the 420MB model on every API request
_chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
_mpnet_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
_collection = _chroma_client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_mpnet_ef,
    metadata={"hnsw:space": "cosine"},
)


def search_schemes(query: str, n_results: int = 5) -> list[dict]:
    """
    Semantic search over scheme documents.

    Args:
        query: user's search query
        n_results: number of results to return

    Returns:
        list of matching documents with metadata
    """

    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=min(n_results, _collection.count()),
    )

    documents = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        documents.append({
            "content": doc,
            "metadata": meta,
            "distance": results["distances"][0][i] if results["distances"] else 0,
        })

    return documents


def chat_answer(question: str, user_context: str = None) -> str:
    """
    RAG-powered Q&A: search ChromaDB for relevant scheme info,
    then use Gemini to generate a contextual answer.

    Args:
        question: user's question about schemes
        user_context: optional user profile context

    Returns:
        answer string
    """

    # Retrieve relevant documents
    docs = search_schemes(question, n_results=5)

    if not docs:
        # Fallback: answer from general knowledge
        context_text = "No specific scheme documents found in the database."
    else:
        context_text = "\n\n---\n\n".join(
            f"**{d['metadata'].get('scheme_name', 'Scheme')}**:\n{d['content']}"
            for d in docs
        )

    user_info = ""
    eligible_schemes_text = ""
    if user_context:
        try:
            profile = json.loads(user_context)
            user_info = f"\n\nUSER PROFILE:\n{json.dumps(profile, indent=2)}"
            
            analysis = run_analysis_with_profile(profile, include_guidance=False)
            eligible_schemes = analysis.get("eligible_schemes", [])
            
            if eligible_schemes:
                top_schemes = eligible_schemes[:5]
                eligible_schemes_text = "\n\nACTUAL ELIGIBLE SCHEMES FOR THIS USER:\n"
                for i, s in enumerate(top_schemes):
                    eligible_schemes_text += f"{i+1}. {s.get('scheme_name')} (Match: {s.get('match_score', 0)}%)\n"
            else:
                eligible_schemes_text = "\n\nACTUAL ELIGIBLE SCHEMES FOR THIS USER: None found based on profile.\n"
        except Exception:
            user_info = f"\n\nUSER CONTEXT:\n{user_context}"

    prompt = f"""
You are a helpful government scheme advisor for Indian citizens.
Answer the user's question using the provided scheme information.

RELEVANT SCHEME INFORMATION FROM SEMANTIC SEARCH:
{context_text}
{eligible_schemes_text}
{user_info}

USER QUESTION:
{question}

Instructions:
- Answer based on the provided scheme information.
- If the user asks about their eligible or top schemes, refer to the 'ACTUAL ELIGIBLE SCHEMES FOR THIS USER' section and list them out. Even if their full details are not in the semantic search results, you MUST list their names and match scores as provided.
- If the information doesn't contain the answer, say so honestly.
- Be specific and cite scheme names when possible.
- Use ₹ for currency amounts.
- Keep the answer concise but complete.
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text.strip()
