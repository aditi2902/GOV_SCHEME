"""
Agent 3: Scheme Discovery / RAG Agent
Uses ChromaDB for semantic search over scheme data.
Powers the chat Q&A and scheme discovery features.
"""

import chromadb
from google import genai
from chromadb.utils import embedding_functions
from config import GEMINI_API_KEY, GEMINI_MODEL, CHROMA_DIR, CHROMA_COLLECTION

client = genai.Client(api_key=GEMINI_API_KEY)

def get_chroma_collection():
    """Get or create the ChromaDB collection."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    
    # Use mpnet-base-v2 which supports 512 tokens and runs locally (no API rate limits)
    mpnet_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")
    
    return chroma_client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=mpnet_ef,
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

    collection = get_chroma_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
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


def chat_answer(question: str, user_context: str = None, eligible_schemes: list[str] = None) -> str:
    """
    RAG-powered Q&A: search ChromaDB for relevant scheme info,
    then use Gemini to generate a contextual answer.

    Args:
        question: user's question about schemes
        user_context: optional user profile context
        eligible_schemes: list of scheme names the user is eligible for

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
    if user_context:
        user_info = f"\n\nUSER PROFILE:\n{user_context}"
        
    if eligible_schemes:
        user_info += f"\n\nELIGIBLE SCHEMES (The user has ALREADY been confirmed eligible for these via deterministic rules):\n"
        user_info += "\n".join(f"- {s}" for s in eligible_schemes[:10])
        user_info += "\n\nCRITICAL RULE: If the user asks what schemes they are eligible for, list the 'ELIGIBLE SCHEMES' provided above. DO NOT evaluate eligibility yourself based on the retrieved documents unless asked about a specific criteria."

    prompt = f"""
You are a helpful government scheme advisor for Indian citizens.
Answer the user's question using the provided scheme information.

RELEVANT SCHEME INFORMATION (Retrieved via semantic search):
{context_text}
{user_info}

USER QUESTION:
{question}

Instructions:
- Answer based on the provided scheme information and user profile.
- If the user asks for schemes they are eligible for, strictly use the ELIGIBLE SCHEMES list provided.
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
