import os
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

    return response.choices[0].message.content
