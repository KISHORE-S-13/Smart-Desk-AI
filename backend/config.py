import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment from backend/.env if available
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)

DEFAULT_DEV_SECRET_KEY = "smartdesk-enterprise-secret-key-2026-production-ready"
DEFAULT_DEV_JWT_SECRET_KEY = "smartdesk-jwt-secret-key-enterprise-32bytes-min-2026"

class Config:
    DEFAULT_DEV_SECRET_KEY = DEFAULT_DEV_SECRET_KEY
    DEFAULT_DEV_JWT_SECRET_KEY = DEFAULT_DEV_JWT_SECRET_KEY

    IS_PRODUCTION = (
        os.getenv("FLASK_ENV") == "production"
        or os.getenv("ENV") == "production"
        or os.getenv("VERCEL") == "1"
        or os.getenv("NODE_ENV") == "production"
    )

    SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_DEV_SECRET_KEY)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", DEFAULT_DEV_JWT_SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Database configuration: support PostgreSQL for production and SQLite for local development
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        # SQLAlchemy 2.0 requires postgresql+psycopg2:// to utilize psycopg2-binary
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        elif DATABASE_URL.startswith("postgresql://") and not DATABASE_URL.startswith("postgresql+"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        DB_PATH = BASE_DIR / "smartdesk.db"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pooling configuration:
    # Serverless environments (like Vercel Lambdas) spin up ephemeral containers.
    # Standard connection pooling (QueuePool) can leak connections or exhaust PostgreSQL max_connections.
    # Under serverless execution (VERCEL=1 or SERVERLESS=1), NullPool closes connections immediately after request completion.
    from sqlalchemy.pool import NullPool
    if os.getenv("VERCEL") or os.getenv("SERVERLESS") or (DATABASE_URL and IS_PRODUCTION):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "poolclass": NullPool,
            "pool_pre_ping": True,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    # Gemini AI configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    # Uploads directory
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload

    @classmethod
    def validate_production_security(cls):
        """
        Validates production configuration: CORS, JWT secrets, and database.
        Raises ValueError if any production security risk is detected.
        Never exposes secret values in logs or exception messages.
        """
        is_prod = (
            os.getenv("FLASK_ENV") == "production"
            or os.getenv("ENV") == "production"
            or os.getenv("VERCEL") == "1"
            or os.getenv("NODE_ENV") == "production"
        )
        if not is_prod:
            return

        # 1. JWT & Secret Key Verification
        secret = os.getenv("SECRET_KEY")
        jwt_secret = os.getenv("JWT_SECRET_KEY")

        if not secret or not secret.strip():
            raise ValueError(
                "Production deployment blocked: SECRET_KEY environment variable is missing or empty. "
                "A secure secret must be configured in production."
            )

        if not jwt_secret or not jwt_secret.strip():
            raise ValueError(
                "Production deployment blocked: JWT_SECRET_KEY environment variable is missing or empty. "
                "A secure secret must be configured in production."
            )

        if secret == DEFAULT_DEV_SECRET_KEY:
            raise ValueError(
                "Production deployment blocked: SECRET_KEY cannot use the default development secret in production. "
                "Configure a unique, cryptographically secure SECRET_KEY."
            )

        if jwt_secret == DEFAULT_DEV_JWT_SECRET_KEY:
            raise ValueError(
                "Production deployment blocked: JWT_SECRET_KEY cannot use the default development secret in production. "
                "Configure a unique, cryptographically secure JWT_SECRET_KEY."
            )

        if len(secret.encode("utf-8")) < 32:
            raise ValueError(
                f"Production deployment blocked: SECRET_KEY is too weak ({len(secret.encode('utf-8'))} bytes). "
                "Must be at least 32 bytes (256 bits) in production."
            )

        if len(jwt_secret.encode("utf-8")) < 32:
            raise ValueError(
                f"Production deployment blocked: JWT_SECRET_KEY is too weak ({len(jwt_secret.encode('utf-8'))} bytes). "
                "Must be at least 32 bytes (256 bits) in production."
            )

        # 2. CORS Verification
        cors_origins = os.getenv("CORS_ORIGINS")
        if not cors_origins or cors_origins.strip() in ("", "*"):
            raise ValueError(
                "Production deployment blocked: In production, CORS_ORIGINS must be explicitly set "
                "to allowed frontend origin(s) (e.g. 'https://smartdesk.vercel.app'). "
                "Wildcard '*' and empty origins are strictly forbidden."
            )

        origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]
        if "*" in origins_list:
            raise ValueError(
                "Production deployment blocked: In production, CORS_ORIGINS cannot contain wildcard '*'."
            )
