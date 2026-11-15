from flask import Blueprint, request, jsonify
from services.ai_service import analyze_ticket_with_gemini
from services.knowledge_service import answer_support_query
from services.auth_service import token_required

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/ai/analyze", methods=["POST"])
@token_required()
def handle_ai_analyze(current_user):
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    impact = data.get("impact", "Medium")
    urgency = data.get("urgency", "Medium")

    if not title:
        return jsonify({"error": "Issue title is required for AI analysis"}), 400

    analysis = analyze_ticket_with_gemini(
        title=title,
        description=description,
        impact=impact,
        urgency=urgency
    )

    return jsonify({"analysis": analysis}), 200


@ai_bp.route("/ai/chat", methods=["POST"])
@token_required()
def handle_ai_chat(current_user):
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Query message cannot be empty"}), 400

    result = answer_support_query(query=message, chat_history=history)

    return jsonify({
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "source_type": result.get("source_type", "local_knowledge_base")
    }), 200
