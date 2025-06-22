from flask import Blueprint, request, jsonify
from services.data_service import extract_measurements, get_event_count, get_all_sites_with_ranges
from services.llm_service import get_llm_response

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
        measurements_list = extract_measurements(site, start_date, end_date)
        if not measurements_list:
            raise ValueError("No data available for selected date range")

        # Take the latest entry for LLM context
        latest = measurements_list[-1]
        measurements = {
            "chl_a": latest["chlorophyll_a"],
            "sst": latest["sea_surface_temperature"],
            "turbidity": latest["turbidity"],
            "probability": latest["bloom_probability"]
        }

        event_count = get_event_count(site, start_date, end_date)

        answer = get_llm_response(
            site=site,
            measurements=measurements,
            event_count=event_count,
            user_question=user_question,
            chat_history=chat_history
        )

        return jsonify({"answer": answer})

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        print("Unhandled Exception:", str(e))
        return jsonify({"error": "Internal server error"}), 500


@api_routes.route('/api/discovery/sites', methods=['GET'])
def get_sites():
    try:
        sites_with_ranges = get_all_sites_with_ranges()
        return jsonify(sites_with_ranges)
    except Exception as e:
        print("Discovery error:", str(e))
        return jsonify({"error": "Failed to get site list"}), 500


@api_routes.route('/api/measurements', methods=['POST'])
def get_measurements():
    data = request.get_json()

    site = data.get('site')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    try:
        measurements = extract_measurements(site, start_date, end_date)
        return jsonify(measurements)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
