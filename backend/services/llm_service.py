import os
import httpx
from dotenv import load_dotenv
import logging
import time

load_dotenv()
logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
MODEL_NAME = "claude-3-5-sonnet-20241022" 

def get_llm_response(site, measurements, event_count, user_question, chat_history=None, additional_context=None):
    """
    Enhanced LLM query with comprehensive HAB site data and environmental conditions.
    """
    
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    if chat_history is None:
        chat_history = []
    
    if additional_context is None:
        additional_context = {}

    system_message = (
        "You are HAB Chat Assistant—an expert marine environmental scientist specializing in harmful algal bloom (HAB) risk assessment. "
        "You have access to comprehensive oceanographic data including satellite observations, environmental conditions, and historical bloom records. "
        "Provide scientific, practical insights tailored to the specific monitoring site. Consider all environmental factors when assessing risk. "
        "Use clear, conversational language while maintaining scientific accuracy. Always acknowledge data limitations when present."
    )

    context_parts = [
        f"🌊 HAB MONITORING REPORT FOR {site.upper()}",
        f"📍 Region: {measurements.get('region', 'Unknown')}",
        f"📊 Data Source: {measurements.get('data_source', 'Unknown')}",
        f"📅 Analysis Period: {additional_context.get('date_range', 'Not specified')}",
        f"📈 Total Records Analyzed: {additional_context.get('total_records', 'Unknown')}",
        "",
        "🔬 CURRENT OCEANOGRAPHIC CONDITIONS:",
        f"• Chlorophyll-a Concentration: {measurements['chl_a']} µg/L",
        f"• Sea Surface Temperature: {measurements['sst']} °C",
        f"• Water Turbidity: {measurements['turbidity']} NTU",
    ]
    
    if measurements.get('salinity') != "N/A":
        context_parts.append(f"• Salinity: {measurements['salinity']} PSU")
    
    if measurements.get('wind_speed') != "N/A":
        context_parts.append(f"• Wind Speed: {measurements['wind_speed']} m/s")
    
    if measurements.get('wave_height') != "N/A":
        context_parts.append(f"• Wave Height: {measurements['wave_height']} m")
    

    context_parts.extend([
        "",
        "⚠️ HAB RISK ASSESSMENT:",
        f"• Bloom Probability: {measurements['probability']} ({measurements.get('risk_level', 'unknown').upper()} risk)",
        f"• Historical HAB Events in Period: {event_count}",
        "",
        f"❓ USER QUESTION: {user_question}"
    ])
    
    context_message = "\n".join(context_parts)


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
        "max_tokens": 1200,  
        "temperature": 0.3,  
        "system": system_message,  
        "messages": messages
    }

    try:
        logger.info(f"Sending LLM request for site: {site}")

        start_time = time.time()

        resp = httpx.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()

        end_time = time.time()
        elapsed_time = end_time - start_time

        logger.info(f"✅ LLM response received in {elapsed_time:.2f} seconds")

        data = resp.json()
        
        response_text = data["content"][0]["text"]
        logger.info(f"LLM response generated successfully ({len(response_text)} characters)")
        
        return response_text
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        error_message = f"API Error: Unable to generate analysis at this time. Please try again."
        if e.response.status_code == 429:
            error_message += " (Rate limit exceeded)"
        elif e.response.status_code == 401:
            error_message += " (Authentication failed)"
        return error_message
        
    except httpx.TimeoutException:
        logger.error("Request timeout")
        return "Analysis timeout: The request took too long to process. Please try with a shorter date range."
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return f"System Error: Unable to generate analysis. Please check your connection and try again."


def get_enhanced_bloom_risk_explanation(measurements):
    """
    Generate a detailed explanation of bloom risk factors based on enhanced measurements
    """
    chl_a = measurements['chl_a']
    sst = measurements['sst']
    turbidity = measurements['turbidity']
    probability = measurements['probability']
    
    explanation_parts = []
    

    if chl_a > 10:
        explanation_parts.append(f"🔴 HIGH chlorophyll-a levels ({chl_a} µg/L) indicate active phytoplankton growth, significantly increasing bloom risk.")
    elif chl_a > 5:
        explanation_parts.append(f"🟡 MODERATE chlorophyll-a levels ({chl_a} µg/L) suggest elevated phytoplankton activity.")
    else:
        explanation_parts.append(f"🟢 LOW chlorophyll-a levels ({chl_a} µg/L) indicate minimal phytoplankton activity.")
    

    if sst > 20:
        explanation_parts.append(f"🌡️ WARM water temperature ({sst}°C) creates favorable conditions for harmful algae.")
    elif sst > 15:
        explanation_parts.append(f"🌡️ MODERATE water temperature ({sst}°C) may support algal growth.")
    else:
        explanation_parts.append(f"🌡️ COOL water temperature ({sst}°C) generally inhibits rapid algal growth.")
    

    if turbidity > 5:
        explanation_parts.append(f"🌫️ HIGH turbidity ({turbidity} NTU) may indicate sediment disturbance or dense phytoplankton.")
    elif turbidity > 2:
        explanation_parts.append(f"🌫️ MODERATE turbidity ({turbidity} NTU) shows some water clarity reduction.")
    else:
        explanation_parts.append(f"💎 LOW turbidity ({turbidity} NTU) indicates clear water conditions.")
    

    if measurements.get('wind_speed') != "N/A":
        wind_speed = measurements['wind_speed']
        if wind_speed > 8:
            explanation_parts.append(f"💨 HIGH wind speeds ({wind_speed} m/s) may help disperse surface blooms.")
        elif wind_speed < 3:
            explanation_parts.append(f"🌊 LOW wind speeds ({wind_speed} m/s) may allow surface bloom accumulation.")
    
    if measurements.get('salinity') != "N/A":
        salinity = measurements['salinity']
        if salinity < 30:
            explanation_parts.append(f"🧂 LOW salinity ({salinity} PSU) may indicate freshwater influence, potentially affecting species composition.")
        elif salinity > 36:
            explanation_parts.append(f"🧂 HIGH salinity ({salinity} PSU) indicates typical marine conditions.")
    
    return "\n".join(explanation_parts)


def generate_mitigation_recommendations(measurements, site, risk_level):
    """
    Generate site-specific mitigation recommendations based on current conditions
    """
    recommendations = []
    
    risk = risk_level.lower()
    
    if risk in ['high', 'critical']:
        recommendations.extend([
            "🚨 IMMEDIATE ACTIONS:",
            "• Issue public health advisory for water contact activities",
            "• Increase monitoring frequency to daily",
            "• Alert local health authorities and water management agencies",
            "• Consider temporary restrictions on shellfish harvesting"
        ])
    
    if risk in ['medium', 'high', 'critical']:
        recommendations.extend([
            "📋 MONITORING ENHANCEMENTS:",
            "• Deploy additional sensors for real-time monitoring",
            "• Collect water samples for species identification",
            "• Monitor oxygen levels and nutrient concentrations"
        ])
    

    region = measurements.get('region', '').lower()
    if 'harbor' in site.lower() or 'bay' in site.lower():
        recommendations.extend([
            "🏘️ COASTAL AREA SPECIFIC:",
            "• Monitor stormwater runoff and nutrient inputs",
            "• Check for sewage outfall contributions",
            "• Consider temporary marina activity restrictions"
        ])
    
    if measurements.get('wind_speed') != "N/A" and measurements['wind_speed'] < 3:
        recommendations.append("🌬️ Consider artificial circulation or aeration in enclosed areas")
    
    return "\n".join(recommendations)



__all__ = ['get_llm_response', 'get_enhanced_bloom_risk_explanation', 'generate_mitigation_recommendations']