import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from backend.app.config import settings
print('MONGODB_URL=', settings.MONGODB_URL)
print('DATABASE_NAME=', settings.DATABASE_NAME)
print('AUTH_BOOTSTRAP_PASSWORD=', 'SET' if settings.AUTH_BOOTSTRAP_PASSWORD else 'UNSET')
