import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_category_insight_from_llm(items):
    """
    items: List of dicts like [{'name': 'Tomatoes', 'price': 30}, ...]
    Returns: Insight string
    """
    # Prepare the prompt
    item_lines = "\n".join([f"- {item['name']} ₹{item['price']}" for item in items])
    prompt = f"""
You are a personal finance assistant. Analyze the following list of items from a grocery bill and:
1. Group them into common household categories (like Vegetables, Dairy, Snacks, Toiletries, Beverages, etc.)
2. Calculate total spent per category
3. Return the result in format: Category: ₹Amount (rounded to 2 decimals)

Items:
{item_lines}

Respond in this format:
Category: Total ₹Amount
"""

    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    if response.ok:
        return response.json().get("response", "").strip()
    else:
        return "LLM failed to generate insight."
