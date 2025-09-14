# search_utils.py
import requests
from openai import OpenAI

# ----------------------------
# Config
# ----------------------------
OPENAI_API = "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"
openai_client = OpenAI(api_key=OPENAI_API)

# Example: Tavily API (can replace with MCP later)
TAVILY_API_KEY = "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"
TAVILY_URL = "https://api.tavily.com/search"

# ----------------------------
# Functions
# ----------------------------
def tavily_search(query: str, max_results: int = 3):
    """
    Perform a web search using Tavily API (can be replaced by MCP server).
    Returns a list of text snippets.
    """
    try:
        headers = {"Authorization": f"Bearer {TAVILY_API_KEY}"}
        payload = {"query": query, "num_results": max_results}

        response = requests.post(TAVILY_URL, json=payload, headers=headers, timeout=20)

        if response.status_code == 200:
            data = response.json()
            results = [item.get("content", "") for item in data.get("results", [])]
            return results
        else:
            print(f"⚠️ Tavily search failed: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


def search_and_generate_answer(query: str):
    """
    Run web search and generate step-by-step answer using OpenAI.
    """
    search_results = tavily_search(query)

    if not search_results:
        return "❌ This question could not be answered using web search."

    context = "\n".join(search_results)

    prompt = f"""
    You are a math professor. Solve the following problem step by step using reliable information.
    Question: {query}
    Context: {context}
    Answer:
    """

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "You are a helpful math professor."},
                      {"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ OpenAI generation failed: {e}")
        return "⚠️ Failed to generate a response."