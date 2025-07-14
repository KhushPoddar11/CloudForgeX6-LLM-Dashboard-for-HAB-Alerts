'''import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_llm_response(site, measurements, user_question):
    prompt = f"""
Here are today's measurements at site {site}:
Chl-a: {measurements['chl_a']} µg/L; SST: {measurements['sst']} °C; Turbidity: {measurements['turbidity']} NTU; Bloom probability: {measurements['probability']}.
User question: {user_question}

Explain why there is a HAB event prediction and suggest two mitigation steps.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )

    return response.choices[0].message.content'''

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL_NAME = "claude-3-5-sonnet-20241022" 

def get_llm_response(site, measurements, event_count, user_question, chat_history=None):
    """
    Query Claude with HAB site data and user question.
    """
    
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    if chat_history is None:
        chat_history = []

    system_message = (
        "You are HAB Chat Assistant—a friendly expert on harmful algal bloom (HAB) risk. "
        "Use the provided data to answer clearly, conversationally, and tailor advice to the specific site. "
        "Provide practical, actionable insights based on the current measurements and historical data."
    )

    context_message = (
        f"Current HAB monitoring data for {site}:\n"
        f"- Chlorophyll-a: {measurements['chl_a']} µg/L\n"
        f"- Sea Surface Temperature: {measurements['sst']} °C\n"
        f"- Turbidity: {measurements['turbidity']} NTU\n"
        f"- Bloom Probability: {measurements['probability']}\n"
        f"- Previous HAB Events: {event_count}\n\n"
        f"User's question: {user_question}"
    )

    messages = []
    
    for msg in chat_history:
        messages.append({
            "role": msg["role"], 
            "content": msg["message"]
        })
    
    messages.append({
        "role": "user",
        "content": context_message
    })

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "max_tokens": 1000,
        "temperature": 0.5,
        "system": system_message,  
        "messages": messages
    }

    try:
        resp = httpx.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        return data["content"][0]["text"]
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"Request failed: {str(e)}")
        raise

