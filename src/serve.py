"""
To start server on prodution.
"""
import os
import sys
import waitress
from core.wsgi import APPLICATION


BASE_DIR = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(BASE_DIR)

os.system('mkdir /tmp/.pyzoho')
os.system('touch /tmp/.pyzoho/zcrm_oauthtokens.pkl')
waitress.serve(
    APPLICATION,
    host='0.0.0.0',
    port=os.getenv('PORT', '8000')
)
