import chromadb
from fastembed import TextEmbedding

COLLECTION_NAME = "schema_store"
embed_model     = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
chroma          = chromadb.Client()


def build_schema_store(documents: list, session_id: str) -> None:
    """Embed column documents and store in ChromaDB for this session."""
    collection_name = f"{COLLECTION_NAME}_{session_id}"

    # clear existing collection for this session if it exists
    try:
        chroma.delete_collection(collection_name)
    except:
        pass

    collection = chroma.create_collection(collection_name)
    embeddings = [e.tolist() for e in embed_model.embed(documents)]

    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=[f"col_{i}" for i in range(len(documents))],
    )


def get_relevant_schema(question: str, session_id: str, table_name: str, n_results: int = 5) -> str:
    """Retrieve the most relevant column descriptions for a question."""
    collection_name = f"{COLLECTION_NAME}_{session_id}"
    collection      = chroma.get_collection(collection_name)

    q_embedding = list(embed_model.embed([question]))[0].tolist()
    results     = collection.query(
        query_embeddings=[q_embedding],
        n_results=n_results,
    )
    docs = results["documents"][0]
    return f"Table: {table_name}\nRelevant columns:\n" + "\n".join(f"  - {d}" for d in docs)