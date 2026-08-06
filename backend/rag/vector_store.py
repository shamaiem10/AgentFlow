import chromadb
from sentence_transformers import SentenceTransformer

# local embedding model — runs on your machine, no API cost
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# persistent Chroma client — saves data to disk so it survives restarts
chroma_client = chromadb.PersistentClient(path="./chroma_data")

def get_org_collection(organization_id):
    """
    Each organization gets its OWN Chroma collection.
    This physically separates tenant data, not just via a filter —
    it's the strongest form of isolation Chroma offers.
    """
    collection_name = f"org_{organization_id}"
    return chroma_client.get_or_create_collection(name=collection_name)

def embed_and_store_chunks(organization_id, document_id, chunks):
    collection = get_org_collection(organization_id)

    texts = chunks
    embeddings = embedding_model.encode(texts).tolist()
    ids = [f"doc{document_id}_chunk{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    return len(chunks)

def search_similar_chunks(organization_id, query, top_k=5):
    collection = get_org_collection(organization_id)
    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    matches = []
    for i in range(len(results["documents"][0])):
        matches.append({
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    return matches