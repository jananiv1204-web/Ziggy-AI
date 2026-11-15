from rag.vector_store import embed_texts


def retrieve_chunks(vector_store, query, k=4):
    if not vector_store:
        return ""

    query_vector = embed_texts([query], "retrieval_query")

    k = min(k, len(vector_store["chunks"]))

    _, ids = vector_store["index"].search(query_vector, k)

    results = [
        vector_store["chunks"][i]
        for i in ids[0]
        if i != -1
    ]

    return "\n\n".join(results)
