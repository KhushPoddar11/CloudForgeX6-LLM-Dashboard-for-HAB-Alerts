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
MODEL_NAME = "claude-3-7-sonnet-20250219"

def get_llm_response(site, measurements, event_count, user_question):
    prompt = f"""
Here are today's measurements at site {site}:
Chl-a: {measurements['chl_a']} µg/L; SST: {measurements['sst']} °C; Turbidity: {measurements['turbidity']} NTU; Bloom probability: {measurements['probability']}.
There have been {event_count} previous HAB events reported for this site in the selected period.

User question: {user_question}

Explain why there is a HAB event prediction and suggest two mitigation steps.
"""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "max_tokens": 1000,
        "temperature": 0.5,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = httpx.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    answer = data["content"][0]["text"]

    return answer
