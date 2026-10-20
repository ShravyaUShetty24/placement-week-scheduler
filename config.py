import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'placement.db')
SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or os.urandom(32).hex()
