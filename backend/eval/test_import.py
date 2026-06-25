import traceback

try:
    from datasets import Dataset
    print("datasets loaded")
    from ragas import evaluate
    print("ragas loaded")
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    print("ragas metrics loaded")
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    print("langchain_google_genai loaded")
    from ragas.llms import LangchainLLMWrapper
    print("ragas.llms loaded")
    from ragas.embeddings import LangchainEmbeddingsWrapper
    print("ragas.embeddings loaded")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    traceback.print_exc()
