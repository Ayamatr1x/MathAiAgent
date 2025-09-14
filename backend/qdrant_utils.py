# qdrant_utils.py
from qdrant_client import QdrantClient
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
QDRANT_URL = "https://860eed44-48cf-41aa-88d7-075924f34685.us-east4-0.gcp.cloud.qdrant.io"
QDRANT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.IRQaj-_1chJ7lg1XmOVAwbbaPOjRp8GuMZ5z7noXqec"
OPENAI_API = "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"

# Initialize clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_KEY, timeout=120.0)
openai_client = OpenAI(api_key=OPENAI_API)

collection_name = "jee_questions"

# ----------------------------
# Functions
# ----------------------------
def embed_text(text: str, model: str = "text-embedding-3-small") -> list:
    """
    Get embedding vector for a given text using OpenAI API.
    """
    embedding = openai_client.embeddings.create(
        input=text,
        model=model
    ).data[0].embedding
    return embedding

def search_qdrant(query: str, top_k: int = 1):
    """
    Search Qdrant collection for most relevant question.
    Returns list of matches with payload & score.
    """
    query_vector = embed_text(query)

    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=top_k
    )
    return results

def insert_point(qid: int, text: str, payload: dict):
    """
    Insert a single point into Qdrant (useful if adding questions later).
    """
    vector = embed_text(text)
    from qdrant_client.http import models

    qdrant_client.upsert(
        collection_name=collection_name,
        points=[models.PointStruct(id=qid, vector=vector, payload=payload)]
    )
    return True

def get_collection_info():
    """
    Get metadata about the collection (size, status, etc.)
    """
    return qdrant_client.get_collection(collection_name)