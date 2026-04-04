"""
Groq AI Integration - Free, Fast LLM API
Using Llama 3.1 70B model
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Configure Groq AI
api_key = os.getenv("GROQ_API_KEY")
client = None

def get_groq_client():
    """Lazy initialization of Groq client"""
    global client
    if client is None and api_key and api_key != "your_groq_api_key_here":
        from groq import Groq
        client = Groq(api_key=api_key)
    return client


def generate_package_with_ai(target_audience: str) -> dict:
    """
    Request AI to create a new specialized hotel package
    based on the target audience prompt.
    """
    groq_client = get_groq_client()
    if not groq_client:
        raise ValueError("Groq API Key not configured. Please set GROQ_API_KEY in .env. Get free key at https://console.groq.com/keys")

    prompt = f"""
You are an expert hospitality revenue manager for a luxury resort in Ethiopia.
We need to create a new custom service package targeting this specific audience/scenario:
"{target_audience}"

Please brainstorm a highly appealing package and return it in pure JSON format (NO markdown formatting, NO ```json wrapping).

The JSON structure MUST exactly match this format:
{{
    "code": "unique_snake_case_code",
    "name": "Catchy Package Name",
    "description": "1 sentence appealing description",
    "category": "romance|family|business|wellness|adventure|conference|cultural|leisure|extended",
    "target_segments": "comma,separated,segments",
    "base_price_etb": 10000,
    "min_discount_pct": 0.05,
    "max_discount_pct": 0.20,
    "min_nights": 2,
    "components": [
        {{
            "service_name": "Name of service",
            "service_category": "spa|dining|activity|room_upgrade|amenity|transfer|venue",
            "description": "Short description",
            "cost_etb": 2000,
            "retail_price_etb": 3500
        }}
    ]
}}

Make the prices in Ethiopian Birr (ETB). 1 USD ~ 55 ETB.
Ensure components complement the target audience beautifully.
Return ONLY raw JSON.
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a hospitality revenue management expert. Always respond with valid JSON only, no markdown formatting."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.7,
            max_tokens=2000,
        )
        
        raw_text = chat_completion.choices[0].message.content.strip()
        
        # Clean up markdown formatting if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        print(f"Failed to parse AI response: {e}")
        raise ValueError(f"Failed to parse AI response: {e}")


def generate_market_insights_with_ai(inventory_data: list) -> str:
    """
    Pass raw occupancy and pricing structured data to AI 
    and ask for strategic revenue management insights.
    """
    groq_client = get_groq_client()
    if not groq_client:
        raise ValueError("Groq API Key not configured. Please set GROQ_API_KEY in .env")

    # We only send a subset of fields to save tokens
    condensed_data = []
    for item in inventory_data[:30]:  # Max 30 entries to keep it concise
        condensed_data.append({
            "date": item.get("date"),
            "room": item.get("room_type_name"),
            "rate_etb": item.get("rate_etb"),
            "occ_pct": round(item.get("occupancy_rate", 0) * 100, 1),
            "demand": item.get("demand_level")
        })

    prompt = f"""
You are the Director of Revenue Management for a luxury resort in Ethiopia.
Look at the following snapshot of our upcoming room inventory and pricing data:

{json.dumps(condensed_data, indent=2)}

Write a brief, sharp, 3-sentence executive summary identifying the biggest revenue opportunity or risk in this dataset. 
Act like an AI alerting the hotel manager. Be specific about dates, room types, or prices.
Format your response as pure text (no markdown formatting). Start directly with the insight.
"""

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a revenue management AI assistant. Provide concise, actionable insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-70b-versatile",
            temperature=0.5,
            max_tokens=500,
        )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI insight generation failed: {e}")
        return "AI analysis temporarily unavailable. Please check your API configuration."
