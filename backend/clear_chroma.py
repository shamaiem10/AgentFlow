from rag.vector_store import chroma_client

collections = chroma_client.list_collections()
print(f"Found {len(collections)} collections.")

for col in collections:
    print(f"Deleting: {col.name}")
    chroma_client.delete_collection(name=col.name)

print("All collections deleted.")