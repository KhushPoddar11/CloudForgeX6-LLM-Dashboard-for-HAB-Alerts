from flask import Blueprint, request, jsonify
from services.llm_service import get_llm_response

api = Blueprint('api', __name__)

@api.route('/api/ask-llm', methods=['POST'])
def ask_llm():
    data = request.json
    site = data['site']
    measurements = data['measurements']
    user_question = data['user_question']
    response = get_llm_response(site, measurements, user_question)
    return jsonify({'answer': response})
