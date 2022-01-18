"""
To start server on prodution.
"""
import os
import sys
import waitress

os.environ.setdefault('ENABLE_BOX_SIGN_TRACKER', 'true')

from core.wsgi import APPLICATION


BASE_DIR = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(BASE_DIR)

waitress.serve(
    APPLICATION,
    host='0.0.0.0',
    port=os.getenv('PORT', '8000')
)
