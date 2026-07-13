def retrieve_chunks(vector_store, query, k=4):
    """
    Retrieve the most relevant chunks from the vector store.
    """

    if vector_store is None:
        return ""

    docs = vector_store.similarity_search(query, k=k)

    if not docs:
        return ""

    context = "\n\n".join(doc.page_content for doc in docs)

    return context