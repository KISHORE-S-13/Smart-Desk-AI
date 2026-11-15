from flask import Blueprint, jsonify
from config import Config
from database import db
from datetime import datetime

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    db_status = "connected"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    has_gemini = bool(Config.GEMINI_API_KEY)
    model_name = Config.GEMINI_MODEL or "gemini-3.8-flash"

    from services.ai_service import get_ai_telemetry
    telemetry = get_ai_telemetry()

    return jsonify({
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "SmartDesk AI – Unified Service Management",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "ai": {
            "gemini_configured": has_gemini,
            "gemini_model": model_name,
            "fallback_enabled": True,
            "concurrency_monitoring": telemetry
        }
    }), 200
