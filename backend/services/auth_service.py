import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import User

def generate_token(user):
    payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "exp": datetime.utcnow() + timedelta(hours=current_app.config.get("JWT_EXPIRATION_HOURS", 24))
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(required_role=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return jsonify({"error": "Authorization header missing"}), 401
            
            parts = auth_header.split(" ")
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return jsonify({"error": "Invalid authorization token format"}), 401

            token = parts[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({"error": "Token is invalid or has expired"}), 401

            from database import db
            current_user = db.session.get(User, payload.get("user_id"))
            if not current_user:
                return jsonify({"error": "User associated with token not found"}), 401

            if required_role and current_user.role != required_role:
                return jsonify({"error": f"Access denied. Requires role: {required_role}"}), 403

            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
