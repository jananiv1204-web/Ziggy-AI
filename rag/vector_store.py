import numpy as np
import faiss
import google.generativeai as genai

EMBED_MODEL = "models/gemini-embedding-001"


def _to_text(chunk):
    if isinstance(chunk, str):
        return chunk
    return getattr(chunk, "page_content", str(chunk))


def embed_texts(texts, task_type):
    vectors = []

    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]

        result = genai.embed_content(
            model=EMBED_MODEL,
            content=batch,
            task_type=task_type
        )

        vectors.extend(result["embedding"])

    array = np.array(vectors, dtype="float32")
    faiss.normalize_L2(array)

    return array


def create_vector_store(chunks):
    texts = [_to_text(c) for c in chunks if _to_text(c).strip()]

    if not texts:
        return None

    embeddings = embed_texts(texts, "retrieval_document")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return {"index": index, "chunks": texts}
