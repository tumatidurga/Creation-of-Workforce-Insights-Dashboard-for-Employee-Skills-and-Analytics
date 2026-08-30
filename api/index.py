import os
import sys

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so that `backend.app` imports work
# when Vercel executes this file from within the `api/` subdirectory.
# ---------------------------------------------------------------------------
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# ---------------------------------------------------------------------------
# Import the FastAPI application. Vercel's Python runtime detects the `app`
# variable and treats it as an ASGI handler.
# ---------------------------------------------------------------------------
from backend.app.main import app  # noqa: E402  (import after sys.path modification)

__all__ = ["app"]
