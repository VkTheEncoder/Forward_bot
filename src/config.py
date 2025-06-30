import os
from dotenv import load_dotenv

load_dotenv()

API_ID   = int(os.getenv('API_ID', 0))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', None)   
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
