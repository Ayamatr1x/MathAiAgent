from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://860eed44-48cf-41aa-88d7-075924f34685.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.IRQaj-_1chJ7lg1XmOVAwbbaPOjRp8GuMZ5z7noXqec"
)

results = client.scroll(collection_name="jee_questions", limit=5)
for point in results[0]:
    print(f"Point ID: {point.id}")
    print(f"Source: {point.payload.get('source', 'Unknown')}")
    print(f"Problem: {point.payload.get('problem', '')[:50]}...")
    print("---")