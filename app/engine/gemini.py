import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini AI
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_package_with_gemini(target_audience: str) -> dict:
    """
    Request Gemini to hallucinate a new specialized hotel package
    based on the target audience prompt.
    """
    if not api_key:
        raise ValueError("Google API Key not configured. Please set GOOGLE_API_KEY in .env")

    model = genai.GenerativeModel('gemini-1.5-flash')
    
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

    response = model.generate_content(prompt)
    
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        print("Failed to parse Gemini response:", response.text)
        raise ValueError(f"Failed to parse AI response: {e}")

def generate_market_insights_with_gemini(inventory_data: list) -> str:
    """
    Pass raw occupancy and pricing structured data to Gemini 
    and ask for strategic revenue management insights.
    """
    if not api_key:
        raise ValueError("Google API Key not configured. Please set GOOGLE_API_KEY in .env")

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # We only send a subset of fields to save tokens
    condensed_data = []
    for item in inventory_data[:30]: # Max 30 entries to keep it concise
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

    response = model.generate_content(prompt)
    return response.text.strip()

