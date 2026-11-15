import sys
from pathlib import Path

# Ensure backend module can be imported by Vercel serverless environment
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app as flask_app

class VercelPrefixMiddleware:
    """
    Ensures both /api/* requests and stripped /* requests route cleanly to Flask blueprints
    in Vercel serverless environments.
    """
    def __init__(self, wsgi_app, prefix="/api"):
        self.wsgi_app = wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if not path.startswith(self.prefix):
            environ["PATH_INFO"] = self.prefix + ("" if path.startswith("/") else "/") + path
        return self.wsgi_app(environ, start_response)

# Vercel looks for the WSGI app instance named 'app'
app = VercelPrefixMiddleware(flask_app.wsgi_app)
