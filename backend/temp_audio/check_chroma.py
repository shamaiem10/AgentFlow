from rag.vector_store import search_similar_chunks

for q in ["What payment methods are accepted?", "your location?"]:
    print(f"QUERY: {q}")
    results = search_similar_chunks(organization_id=1, query=q, top_k=3)
    for r in results:
        print(f"  distance={r['distance']:.4f}  content={r['content'][:200]}")
    print()