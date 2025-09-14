import json
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer
import argparse
import time

# Initialize Qdrant client with cloud URL and API key
COLLECTION_NAME = "jee_questions"
QDRANT_URL = "https://860eed44-48cf-41aa-88d7-075924f34685.us-east4-0.gcp.cloud.qdrant.io:6333"
QDRANT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.IRQaj-_1chJ7lg1XmOVAwbbaPOjRp8GuMZ5z7noXqec"
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Initialize embedding model (produces 384-dimensional vectors)
model = SentenceTransformer('all-MiniLM-L6-v2')

def ensure_collection():
    """Create or verify the collection exists with correct config."""
    try:
        info = client.get_collection(COLLECTION_NAME)
        print(f"📊 Collection '{COLLECTION_NAME}' exists with {info.config.params.vectors.size} dimensions.")
        if info.config.params.vectors.size != 384:
            print("⚠️ Dimension mismatch. Recreating collection.")
            client.delete_collection(COLLECTION_NAME)
            raise ValueError("Recreate needed.")
    except Exception:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"✅ Created collection '{COLLECTION_NAME}' with 384 dimensions.")

def insert_point(qid, text, payload, max_retries=3):
    """Insert point with retries on connection errors."""
    vector = model.encode(text).tolist()
    print(f"🔍 Generated vector for entry {qid} with dimension: {len(vector)}")
    
    for attempt in range(max_retries):
        try:
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[{"id": qid, "vector": vector, "payload": payload}]
            )
            return True
        except Exception as e:
            if "Connection" in str(e) or "10061" in str(e) or "503" in str(e):
                print(f"⚠️ Connection error on attempt {attempt + 1}/{max_retries} for entry {qid}. Retrying in 5s...")
                time.sleep(5)
            else:
                print(f"❌ Non-connection error for entry {qid}: {e}")
                return False
    print(f"❌ Failed to insert entry {qid} after {max_retries} retries.")
    return False

def get_collection_info():
    try:
        info = client.get_collection(COLLECTION_NAME)
        return info.dict()
    except Exception as e:
        print(f"❌ Error retrieving collection info: {e}")
        return None

def main(limit):
    # Test initial connection
    try:
        client.get_collections()
        print("✅ Connected to Qdrant cloud server.")
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant: {e}")
        print(f"💡 Ensure the Qdrant URL ({QDRANT_URL}) and API key are correct.")
        exit(1)

    # Ensure collection
    ensure_collection()

    # Load dataset
    try:
        df = pd.read_parquet(
            "hf://datasets/qwedsacf/competition_math/data/train-00000-of-00001-7320a6f3aba8ebd2.parquet"
        )
        print(f"📥 Loaded dataset with {len(df)} rows")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        exit(1)

    dataset = df.to_dict(orient="records")
    dataset = dataset[:limit]
    print(f"📏 Limited dataset to {len(dataset)} rows")

    # Insert entries
    for idx, entry in enumerate(dataset, start=1):
        text = f"{entry.get('problem', '')} (Gold: {entry.get('solution', '')})"
        payload = {
            "problem": entry.get("problem"),
            "solution": entry.get("solution"),
            "level": entry.get("level"),
            "type": entry.get("type"),
            "source": "Knowledge Base"
        }
        success = insert_point(qid=idx, text=text, payload=payload)
        if success:
            print(f"✅ Inserted entry {idx}: {entry.get('problem', '')[:50]}...")
        else:
            print(f"⚠️ Failed to insert entry {idx}")

    # Verify collection
    info = get_collection_info()
    if info:
        print(f"📊 Collection info:\n{json.dumps(info, indent=2)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload math competition dataset to Qdrant")
    parser.add_argument("--limit", type=int, default=150, help="Number of questions to process")
    args = parser.parse_args()
    main(args.limit)