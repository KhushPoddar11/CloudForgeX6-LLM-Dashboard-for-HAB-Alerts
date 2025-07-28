# from flask import Blueprint, request, jsonify
# from services.data_service import extract_measurements, get_event_count, get_all_sites_with_ranges
# from services.llm_service import get_llm_response

# api_routes = Blueprint('api_routes', __name__)

# @api_routes.route('/api/ask-llm', methods=['POST'])
# def ask_llm():
#     data = request.get_json()

#     site = data.get('site')
#     start_date = data.get('start_date')
#     end_date = data.get('end_date')
#     user_question = data.get('user_question')
#     chat_history = data.get('chat_history', [])

#     if not site or not start_date or not end_date or not user_question:
#         return jsonify({"error": "Missing required fields"}), 400

#     try:
#         measurements_list = extract_measurements(site, start_date, end_date)
#         if not measurements_list:
#             raise ValueError("No data available for selected date range")

#         latest = measurements_list[-1]
#         measurements = {
#             "chl_a": latest["chlorophyll_a"],
#             "sst": latest["sea_surface_temperature"],
#             "turbidity": latest["turbidity"],
#             "probability": latest["bloom_probability"]
#         }

#         event_count = get_event_count(site, start_date, end_date)

#         answer = get_llm_response(
#             site=site,
#             measurements=measurements,
#             event_count=event_count,
#             user_question=user_question,
#             chat_history=chat_history
#         )

#         return jsonify({"answer": answer})

#     except ValueError as e:
#         return jsonify({"error": str(e)}), 404

#     except Exception as e:
#         print("Unhandled Exception:", str(e))
#         return jsonify({"error": "Internal server error"}), 500


# @api_routes.route('/api/discovery/sites', methods=['GET'])
# def get_sites():
#     try:
#         sites_with_ranges = get_all_sites_with_ranges()
#         return jsonify(sites_with_ranges)
#     except Exception as e:
#         print("Discovery error:", str(e))
#         return jsonify({"error": "Failed to get site list"}), 500


# @api_routes.route('/api/measurements', methods=['POST'])
# def get_measurements():
#     data = request.get_json()

#     site = data.get('site')
#     start_date = data.get('start_date')
#     end_date = data.get('end_date')

#     try:
#         measurements = extract_measurements(site, start_date, end_date)
#         return jsonify(measurements)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

from flask import Blueprint, request, jsonify
from services.data_service import (
    extract_measurements, 
    get_event_count, 
    get_all_sites_with_ranges,
    get_site_summary_stats
)
from services.llm_service import get_llm_response
import logging

logger = logging.getLogger(__name__)
api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/api/ask-llm', methods=['POST'])
def ask_llm():
    data = request.get_json()

    site = data.get('site')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    user_question = data.get('user_question')
    chat_history = data.get('chat_history', [])

    if not site or not start_date or not end_date or not user_question:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Get measurements with limit for LLM context
        measurements_list = extract_measurements(site, start_date, end_date, limit=50)
        if not measurements_list:
            raise ValueError("No data available for selected date range")

        # Get latest measurement for current conditions
        latest = measurements_list[0]  # Already sorted by timestamp desc
        
        # Enhanced measurements with new fields
        measurements = {
            "chl_a": latest["chlorophyll_a"],
            "sst": latest["sea_surface_temperature"],
            "turbidity": latest["turbidity"],
            "salinity": latest.get("salinity", "N/A"),
            "wind_speed": latest.get("wind_speed", "N/A"),
            "wave_height": latest.get("wave_height", "N/A"),
            "probability": latest["bloom_probability"],
            "risk_level": latest.get("risk_level", "unknown"),
            "data_source": latest.get("dataset_source", "unknown"),
            "region": latest.get("region", "unknown")
        }

        event_count = get_event_count(site, start_date, end_date)

        # Enhanced LLM response with more context
        answer = get_llm_response(
            site=site,
            measurements=measurements,
            event_count=event_count,
            user_question=user_question,
            chat_history=chat_history,
            additional_context={
                "total_records": len(measurements_list),
                "date_range": f"{start_date} to {end_date}",
                "region": measurements["region"]
            }
        )

        return jsonify({"answer": answer})

    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Unhandled Exception in ask_llm: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@api_routes.route('/api/discovery/sites', methods=['GET'])
def get_sites():
    """Enhanced site discovery with metadata"""
    try:
        sites_with_ranges = get_all_sites_with_ranges()
        return jsonify(sites_with_ranges)
    except Exception as e:
        logger.error(f"Discovery error: {str(e)}")
        return jsonify({"error": "Failed to get site list"}), 500


@api_routes.route('/api/measurements', methods=['POST'])
def get_measurements():
    """Get measurements with pagination support"""
    data = request.get_json()

    site = data.get('site')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    limit = data.get('limit', 1000)  # Default limit
    
    try:
        measurements = extract_measurements(site, start_date, end_date, limit=limit)
        
        # Add metadata about the results
        response = {
            "measurements": measurements,
            "metadata": {
                "count": len(measurements),
                "limited": len(measurements) == limit,
                "site": site,
                "date_range": f"{start_date} to {end_date}"
            }
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in get_measurements: {str(e)}")
        return jsonify({"error": str(e)}), 400


@api_routes.route('/api/summary', methods=['GET'])
def get_dataset_summary():
    """New endpoint for dataset overview"""
    try:
        summary = get_site_summary_stats()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        return jsonify({"error": "Failed to get dataset summary"}), 500


@api_routes.route('/api/sites/<site_name>/stats', methods=['GET'])
def get_site_specific_stats(site_name):
    """Get detailed statistics for a specific site"""
    try:
        # Get date range from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({"error": "start_date and end_date are required"}), 400
        
        # Get measurements for the site
        measurements = extract_measurements(site_name, start_date, end_date, limit=10000)
        
        if not measurements:
            return jsonify({"error": "No data found for this site and date range"}), 404
        
        # Calculate statistics
        import pandas as pd
        df = pd.DataFrame(measurements)
        
        stats = {
            "site_name": site_name,
            "total_records": len(df),
            "date_range": {
                "start": df['timestamp'].min(),
                "end": df['timestamp'].max()
            },
            "chlorophyll_stats": {
                "mean": float(df['chlorophyll_a'].mean()),
                "median": float(df['chlorophyll_a'].median()),
                "std": float(df['chlorophyll_a'].std()),
                "min": float(df['chlorophyll_a'].min()),
                "max": float(df['chlorophyll_a'].max())
            },
            "environmental_conditions": {
                "avg_sst": float(df['sea_surface_temperature'].mean()),
                "avg_turbidity": float(df['turbidity'].mean()),
                "avg_salinity": float(df['salinity'].mean()) if 'salinity' in df.columns else None,
                "avg_wind_speed": float(df['wind_speed'].mean()) if 'wind_speed' in df.columns else None,
                "avg_wave_height": float(df['wave_height'].mean()) if 'wave_height' in df.columns else None
            },
            "risk_analysis": {
                "avg_bloom_probability": float(df['bloom_probability'].mean()),
                "risk_distribution": df['risk_level'].value_counts().to_dict() if 'risk_level' in df.columns else {},
                "bloom_events": int(df['bloom_label'].sum()) if 'bloom_label' in df.columns else 0
            },
            "data_sources": df['dataset_source'].value_counts().to_dict() if 'dataset_source' in df.columns else {}
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting site stats: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_routes.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        summary = get_site_summary_stats()
        return jsonify({
            "status": "healthy",
            "dataset_loaded": bool(summary),
            "total_records": summary.get("total_records", 0) if summary else 0,
            "unique_sites": summary.get("unique_sites", 0) if summary else 0
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500