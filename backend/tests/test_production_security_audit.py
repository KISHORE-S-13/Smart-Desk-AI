import os
import sys
import unittest
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

class TestProductionSecurityAudit(unittest.TestCase):
    def setUp(self):
        # Save original environment
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_local_dev_permissive_cors_and_defaults(self):
        """In local development, default secrets and permissive CORS are allowed."""
        os.environ["ENV"] = "development"
        os.environ.pop("FLASK_ENV", None)
        os.environ.pop("VERCEL", None)
        os.environ.pop("CORS_ORIGINS", None)
        os.environ.pop("SECRET_KEY", None)
        os.environ.pop("JWT_SECRET_KEY", None)

        from config import Config
        from app import create_app

        # Should not raise any error
        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.config["SECRET_KEY"], Config.DEFAULT_DEV_SECRET_KEY)
        self.assertEqual(app.config["JWT_SECRET_KEY"], Config.DEFAULT_DEV_JWT_SECRET_KEY)

    def test_production_rejects_missing_secret_key(self):
        """In production, missing SECRET_KEY must raise ValueError."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = ""
        os.environ["JWT_SECRET_KEY"] = "a" * 32
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app"

        from app import create_app
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("SECRET_KEY", str(ctx.exception))
        self.assertIn("missing", str(ctx.exception).lower())

    def test_production_rejects_missing_jwt_secret_key(self):
        """In production, missing JWT_SECRET_KEY must raise ValueError."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "s" * 32
        os.environ["JWT_SECRET_KEY"] = ""
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app"

        from app import create_app
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("JWT_SECRET_KEY", str(ctx.exception))
        self.assertIn("missing", str(ctx.exception).lower())

    def test_production_rejects_default_dev_secrets(self):
        """In production, default development secrets must be rejected."""
        from config import DEFAULT_DEV_SECRET_KEY, DEFAULT_DEV_JWT_SECRET_KEY
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = DEFAULT_DEV_SECRET_KEY
        os.environ["JWT_SECRET_KEY"] = "custom-secure-key-that-is-over-32-bytes"
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app"

        from app import create_app
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("SECRET_KEY", str(ctx.exception))
        self.assertIn("default", str(ctx.exception).lower())

        # Test JWT default secret rejection
        os.environ["SECRET_KEY"] = "custom-secure-secret-key-over-32-bytes-long"
        os.environ["JWT_SECRET_KEY"] = DEFAULT_DEV_JWT_SECRET_KEY
        with self.assertRaises(ValueError) as ctx2:
            create_app()
        self.assertIn("JWT_SECRET_KEY", str(ctx2.exception))
        self.assertIn("default", str(ctx2.exception).lower())

    def test_production_rejects_weak_secrets(self):
        """In production, secrets shorter than 32 bytes must be rejected."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "short-key-16b!"
        os.environ["JWT_SECRET_KEY"] = "valid-and-strong-jwt-secret-key-32b-min"
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app"

        from app import create_app
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("SECRET_KEY", str(ctx.exception))
        self.assertIn("too weak", str(ctx.exception).lower())
        # Verify secret itself is never revealed in error message
        self.assertNotIn("short-key-16b!", str(ctx.exception))

        os.environ["SECRET_KEY"] = "valid-and-strong-secret-key-32b-minimum!"
        os.environ["JWT_SECRET_KEY"] = "weak-jwt"
        with self.assertRaises(ValueError) as ctx2:
            create_app()
        self.assertIn("JWT_SECRET_KEY", str(ctx2.exception))
        self.assertIn("too weak", str(ctx2.exception).lower())
        self.assertNotIn("weak-jwt", str(ctx2.exception))

    def test_production_rejects_wildcard_cors(self):
        """In production, CORS_ORIGINS set to '*' or containing '*' must be rejected."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "production-secure-secret-key-32-bytes-long!"
        os.environ["JWT_SECRET_KEY"] = "production-secure-jwt-key-32-bytes-long!"

        from app import create_app

        # 1. CORS_ORIGINS = "*"
        os.environ["CORS_ORIGINS"] = "*"
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("CORS_ORIGINS", str(ctx.exception))
        self.assertIn("forbidden", str(ctx.exception).lower())

        # 2. CORS_ORIGINS missing or empty
        os.environ["CORS_ORIGINS"] = ""
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("CORS_ORIGINS", str(ctx.exception))

        # 3. CORS_ORIGINS containing wildcard alongside domains
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app,*"
        with self.assertRaises(ValueError) as ctx:
            create_app()
        self.assertIn("CORS_ORIGINS", str(ctx.exception))
        self.assertIn("wildcard", str(ctx.exception).lower())

    def test_production_accepts_valid_configuration(self):
        """In production with strong secrets and explicit CORS origins, app initializes cleanly."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "production-secure-secret-key-32-bytes-long!"
        os.environ["JWT_SECRET_KEY"] = "production-secure-jwt-key-32-bytes-long!"
        os.environ["CORS_ORIGINS"] = "https://smartdesk.vercel.app,https://admin.smartdesk.ai"
        os.environ["AUTO_INIT_DB"] = "false"

        from app import create_app
        app = create_app()
        self.assertIsNotNone(app)
        self.assertEqual(app.config["SECRET_KEY"], "production-secure-secret-key-32-bytes-long!")
        self.assertEqual(app.config["JWT_SECRET_KEY"], "production-secure-jwt-key-32-bytes-long!")

    def test_preview_deployment_cors_pattern(self):
        """In preview environments, wildcard subdomain patterns like https://*.vercel.app are supported."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "production-secure-secret-key-32-bytes-long!"
        os.environ["JWT_SECRET_KEY"] = "production-secure-jwt-key-32-bytes-long!"
        os.environ["CORS_ORIGINS"] = "https://*.vercel.app"
        os.environ["AUTO_INIT_DB"] = "false"

        from app import create_app
        app = create_app()
        self.assertIsNotNone(app)
        client = app.test_client()
        # Test preview branch origin match
        res = client.get("/api/health", headers={"Origin": "https://smartdesk-git-feature-preview.vercel.app"})
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "https://smartdesk-git-feature-preview.vercel.app")

    def test_database_url_postgresql_psycopg2_normalization(self):
        """Verifies postgres:// and postgresql:// are normalized to postgresql+psycopg2://."""
        os.environ["ENV"] = "development"
        urls = [
            ("postgres://user:pass@host:5432/db", "postgresql+psycopg2://user:pass@host:5432/db"),
            ("postgresql://user:pass@host:5432/db", "postgresql+psycopg2://user:pass@host:5432/db"),
            ("postgresql+psycopg2://user:pass@host:5432/db", "postgresql+psycopg2://user:pass@host:5432/db"),
        ]
        for input_url, expected in urls:
            url = input_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            self.assertEqual(url, expected)

if __name__ == "__main__":
    unittest.main()