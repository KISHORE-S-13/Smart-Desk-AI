import os
import re
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import db
from seed_data import initialize_database

# Import blueprints
from routes.auth_routes import auth_bp
from routes.ticket_routes import ticket_bp
from routes.dashboard_routes import dashboard_bp
from routes.ai_routes import ai_bp
from routes.knowledge_routes import knowledge_bp
from routes.health_routes import health_bp

def create_app():
    # Validate production security and configuration if running in production mode
    Config.validate_production_security()

    app = Flask(__name__)
    app.config.from_object(Config)

    # Sync runtime secret keys from environment
    if os.getenv("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    if os.getenv("JWT_SECRET_KEY"):
        app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    # Configure CORS: Permissive only for local development; strictly explicit in production
    is_prod = (
        os.getenv("FLASK_ENV") == "production"
        or os.getenv("ENV") == "production"
        or os.getenv("VERCEL") == "1"
        or os.getenv("NODE_ENV") == "production"
    )

    def parse_cors_origin(o):
        if "*" in o and o != "*":
            pattern = "^" + re.escape(o).replace(r"\*", r"[a-zA-Z0-9_\-]+") + "$"
            return re.compile(pattern)
        return o

    cors_origins_env = os.getenv("CORS_ORIGINS")
    if is_prod:
        # In production mode, validate_production_security() has already verified CORS_ORIGINS is not empty or bare '*'
        cors_origins = [parse_cors_origin(o.strip()) for o in cors_origins_env.split(",") if o.strip()]
    else:
        # Development mode: default to "*" if unset or "*"
        if not cors_origins_env or cors_origins_env.strip() == "*":
            cors_origins = "*"
        else:
            cors_origins = [parse_cors_origin(o.strip()) for o in cors_origins_env.split(",") if o.strip()]

    CORS(app, resources={r"/api/*": {"origins": cors_origins}}, supports_credentials=True)

    # Initialize SQLAlchemy
    db.init_app(app)

    # Register blueprints under /api prefix
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(ticket_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")
    app.register_blueprint(ai_bp, url_prefix="/api")
    app.register_blueprint(knowledge_bp, url_prefix="/api")

    # Global error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    # Auto-initialize database on application startup:
    # In production/serverless, default is False to eliminate cold-start DDL latency and concurrent locks.
    # In local development, default is True for automatic zero-config setup.
    default_auto_init = "false" if is_prod else "true"
    auto_init = os.getenv("AUTO_INIT_DB", default_auto_init).lower() in ("true", "1")
    if auto_init:
        with app.app_context():
            initialize_database()

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
