import os
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

os.environ["FASTEMBED_CACHE_PATH"] = "./fastembed_cache"

COLLECTION_NAME = "schema_store"
chroma          = chromadb.Client()
ef              = DefaultEmbeddingFunction()


def build_schema_store(documents: list, session_id: str) -> None:
    """Embed column documents and store in ChromaDB for this session."""
    collection_name = f"{COLLECTION_NAME}_{session_id}"

    try:
        chroma.delete_collection(collection_name)
    except:
        pass

    collection = chroma.create_collection(collection_name, embedding_function=ef)
    collection.add(
        documents=documents,
        ids=[f"col_{i}" for i in range(len(documents))],
    )


def get_relevant_schema(question: str, session_id: str, table_name: str, n_results: int = 5) -> str:
    """Retrieve the most relevant column descriptions for a question."""
    collection_name = f"{COLLECTION_NAME}_{session_id}"
    collection      = chroma.get_collection(collection_name, embedding_function=ef)

    results = collection.query(
        query_texts=[question],
        n_results=n_results,
    )
    docs = results["documents"][0]
    return f"Table: {table_name}\nRelevant columns:\n" + "\n".join(f"  - {d}" for d in docs)