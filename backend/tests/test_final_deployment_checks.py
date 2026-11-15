import os
import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from flask import Flask

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import db
from models import User, KnowledgeArticle
from seed_data import initialize_database

class TestFinalDeploymentChecks(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    # =========================================================================
    # CHECK 1: PostgreSQL Advisory Lock Lifecycle & Guaranteed Lock Release
    # =========================================================================
    def test_postgres_advisory_lock_lifecycle_acquired(self):
        """Verifies advisory lock is acquired, seeding runs, and lock is released in finally."""
        from app import create_app
        app = create_app()

        with app.app_context():
            mock_conn = MagicMock()
            # Mock pg_try_advisory_lock returning True (lock acquired)
            mock_conn.execute.return_value.scalar.return_value = True

            mock_engine = MagicMock()
            mock_engine.dialect.name = "postgresql"
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            with patch.object(type(db), "engine", new_callable=PropertyMock, return_value=mock_engine), \
                 patch.object(db, "create_all") as mock_create, \
                 patch("seed_data.seed_demo_users") as mock_users, \
                 patch("seed_data.seed_knowledge_base") as mock_kb:

                initialize_database()

                # Verify lock attempt
                first_call_sql = str(mock_conn.execute.call_args_list[0][0][0])
                self.assertIn("pg_try_advisory_lock", first_call_sql)
                self.assertIn("847291", first_call_sql)

                # Verify operations ran
                mock_create.assert_called_once()
                mock_users.assert_called_once()
                mock_kb.assert_called_once()

                # Verify guaranteed release in finally block
                last_call_sql = str(mock_conn.execute.call_args_list[-1][0][0])
                self.assertIn("pg_advisory_unlock", last_call_sql)
                self.assertIn("847291", last_call_sql)
                mock_conn.commit.assert_called()

    def test_postgres_advisory_lock_concurrent_skips_cleanly(self):
        """Verifies when lock is held by another instance (returns False), execution skips cleanly."""
        from app import create_app
        app = create_app()

        with app.app_context():
            mock_conn = MagicMock()
            # Mock pg_try_advisory_lock returning False (concurrent run in progress)
            mock_conn.execute.return_value.scalar.return_value = False

            mock_engine = MagicMock()
            mock_engine.dialect.name = "postgresql"
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            with patch.object(type(db), "engine", new_callable=PropertyMock, return_value=mock_engine), \
                 patch.object(db, "create_all") as mock_create, \
                 patch("seed_data.seed_demo_users") as mock_users, \
                 patch("seed_data.seed_knowledge_base") as mock_kb:

                initialize_database()

                # Verify lock attempt was made
                first_call_sql = str(mock_conn.execute.call_args_list[0][0][0])
                self.assertIn("pg_try_advisory_lock", first_call_sql)

                # Critical: DDL and seeding must NOT have been called!
                mock_create.assert_not_called()
                mock_users.assert_not_called()
                mock_kb.assert_not_called()

    def test_postgres_advisory_lock_guaranteed_release_on_error(self):
        """Verifies lock is guaranteed to be released even if table creation or seeding raises an error."""
        from app import create_app
        app = create_app()

        with app.app_context():
            mock_conn = MagicMock()
            mock_conn.execute.return_value.scalar.return_value = True

            mock_engine = MagicMock()
            mock_engine.dialect.name = "postgresql"
            mock_engine.connect.return_value.__enter__.return_value = mock_conn

            with patch.object(type(db), "engine", new_callable=PropertyMock, return_value=mock_engine), \
                 patch.object(db, "create_all", side_effect=RuntimeError("Database failure simulated")):

                with self.assertRaises(RuntimeError):
                    initialize_database()

                # Guaranteed lock release must still be called in finally block
                unlock_calls = [
                    call for call in mock_conn.execute.call_args_list
                    if "pg_advisory_unlock" in str(call[0][0])
                ]
                self.assertTrue(len(unlock_calls) >= 1, "pg_advisory_unlock was not called in finally!")

    # =========================================================================
    # CHECK 2: Preview CORS Regex Matching & Rejection of Unauthorized Origins
    # =========================================================================
    def test_preview_cors_allowed_and_unauthorized_rejections(self):
        """Verifies preview wildcard pattern allows legitimate Vercel preview origins and rejects all unauthorized origins."""
        os.environ["ENV"] = "production"
        os.environ["SECRET_KEY"] = "production-secure-secret-key-32-bytes-long!"
        os.environ["JWT_SECRET_KEY"] = "production-secure-jwt-key-32-bytes-long!"
        os.environ["CORS_ORIGINS"] = "https://*.vercel.app,https://smartdesk-production.vercel.app"
        os.environ["AUTO_INIT_DB"] = "false"

        from app import create_app
        app = create_app()
        client = app.test_client()

        # Authorized Preview & Production Domains
        authorized = [
            "https://smartdesk-production.vercel.app",
            "https://smartdesk-preview-pr12.vercel.app",
            "https://smartdesk-git-feature-preview.vercel.app",
            "https://branch-deploy-123.vercel.app",
        ]
        for origin in authorized:
            res = client.get("/api/health", headers={"Origin": origin})
            self.assertEqual(
                res.headers.get("Access-Control-Allow-Origin"),
                origin,
                f"Failed to allow legitimate preview origin: {origin}"
            )

        # Unauthorized / Malicious Domains
        unauthorized = [
            "https://evil-attacker.com",
            "https://attacker.vercel.app.evil.com",       # Subdomain suffix trick
            "https://vercel.app.attacker.com",
            "http://smartdesk-preview-pr12.vercel.app",   # Insecure HTTP
            "https://malicious.org",
            "https://phishing-smartdesk.com",
            "http://localhost:3000",
        ]
        for origin in unauthorized:
            res = client.get("/api/health", headers={"Origin": origin})
            self.assertNotEqual(
                res.headers.get("Access-Control-Allow-Origin"),
                origin,
                f"Security breach: Unauthorized origin was allowed! {origin}"
            )
            self.assertIsNone(
                res.headers.get("Access-Control-Allow-Origin"),
                f"Origin header must be omitted for unauthorized origin: {origin}"
            )

    # =========================================================================
    # CHECK 3: Fresh Database Seeding & Strict Idempotency Across Multiple Runs
    # =========================================================================
    def test_seed_data_fresh_schema_and_idempotency(self):
        """Verifies initialize_database works cleanly on fresh database and is strictly idempotent when run repeatedly."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
            temp_db_path = tf.name

        test_app = Flask(__name__)
        test_app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{temp_db_path}"
        test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        db.init_app(test_app)

        try:
            # RUN 1: Fresh Database Initialization
            with test_app.app_context():
                initialize_database()
                users_pass1 = User.query.all()
                articles_pass1 = KnowledgeArticle.query.all()

                self.assertEqual(len(users_pass1), 2, "Fresh seed must create exactly 2 demo users.")
                self.assertEqual(len(articles_pass1), 5, "Fresh seed must create exactly 5 default articles.")
                
                # Verify demo account details
                emails = {u.email: u.role for u in users_pass1}
                self.assertEqual(emails.get("employee@smartdesk.ai"), "employee")
                self.assertEqual(emails.get("admin@smartdesk.ai"), "admin")

            # RUN 2: Re-executing initialize_database on already populated database (Idempotency)
            with test_app.app_context():
                initialize_database()
                users_pass2 = User.query.all()
                articles_pass2 = KnowledgeArticle.query.all()

                # Must not duplicate users or articles
                self.assertEqual(len(users_pass2), 2, "Run 2 must not duplicate demo users!")
                self.assertEqual(len(articles_pass2), 5, "Run 2 must not duplicate knowledge articles!")

            # RUN 3: Third consecutive execution to guarantee continuous idempotency
            with test_app.app_context():
                initialize_database()
                users_pass3 = User.query.all()
                articles_pass3 = KnowledgeArticle.query.all()

                self.assertEqual(len(users_pass3), 2, "Run 3 must remain strictly idempotent!")
                self.assertEqual(len(articles_pass3), 5, "Run 3 must remain strictly idempotent!")

        finally:
            with test_app.app_context():
                db.session.remove()
                db.engine.dispose()
            if os.path.exists(temp_db_path):
                os.remove(temp_db_path)

if __name__ == "__main__":
    unittest.main()