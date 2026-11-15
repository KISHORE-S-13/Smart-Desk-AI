from database import db
from models import User
from services.knowledge_service import seed_knowledge_base

def seed_demo_users():
    """Seeds default demo employee and admin accounts if they do not exist."""
    users_data = [
        {
            "name": "Alex Rivera",
            "email": "employee@smartdesk.ai",
            "password": "Employee@123",
            "role": "employee",
            "department": "Engineering"
        },
        {
            "name": "Sarah Chen",
            "email": "admin@smartdesk.ai",
            "password": "Admin@123",
            "role": "admin",
            "department": "IT Operations"
        }
    ]

    for u in users_data:
        existing = User.query.filter_by(email=u["email"]).first()
        if not existing:
            user = User(
                name=u["name"],
                email=u["email"],
                role=u["role"],
                department=u["department"]
            )
            user.set_password(u["password"])
            db.session.add(user)
            print(f"[SmartDesk AI] Created demo {u['role']} user: {u['email']}")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[SmartDesk AI] User seeding error: {e}")

def ensure_schema_compatibility():
    """Ensures is_deleted column exists on tickets table in existing databases."""
    from sqlalchemy import text, inspect
    try:
        inspector = inspect(db.engine)
        if "tickets" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("tickets")]
            if "is_deleted" not in cols:
                is_postgres = db.engine.dialect.name == "postgresql"
                with db.engine.begin() as conn:
                    default_val = "FALSE" if is_postgres else "0"
                    conn.execute(text(f"ALTER TABLE tickets ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT {default_val}"))
                print("[SmartDesk AI] Schema migrated: Added is_deleted column to tickets.")
    except Exception as e:
        print(f"[SmartDesk AI] Schema migration note: {e}")

def initialize_database():
    """
    Initializes tables and seeds initial data.
    If executed against PostgreSQL, uses an advisory lock to prevent concurrent runs.
    """
    engine = db.engine
    is_postgres = engine.dialect.name == "postgresql"

    if is_postgres:
        from sqlalchemy import text
        with engine.connect() as conn:
            # PostgreSQL advisory lock ID for SmartDesk database initialization: 847291
            acquired = conn.execute(text("SELECT pg_try_advisory_lock(847291)")).scalar()
            if not acquired:
                print("[SmartDesk AI] Database initialization already in progress on another instance. Skipping.")
                return
            try:
                db.create_all()
                ensure_schema_compatibility()
                seed_demo_users()
                seed_knowledge_base()
                print("[SmartDesk AI] Database tables created and demo data seeded successfully (PostgreSQL).")
            finally:
                try:
                    conn.execute(text("SELECT pg_advisory_unlock(847291)"))
                    conn.commit()
                except Exception:
                    try:
                        conn.rollback()
                        conn.execute(text("SELECT pg_advisory_unlock(847291)"))
                        conn.commit()
                    except Exception:
                        pass  # Closing conn when context exits unconditionally releases session advisory locks in PostgreSQL
    else:
        db.create_all()
        ensure_schema_compatibility()
        seed_demo_users()
        seed_knowledge_base()
        print("[SmartDesk AI] Database initialized and seeded successfully.")

if __name__ == "__main__":
    import sys
    from pathlib import Path
    backend_dir = Path(__file__).resolve().parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from app import create_app
    app = create_app()
    with app.app_context():
        initialize_database()
