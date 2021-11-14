import os

from dotenv import load_dotenv

load_dotenv(".env")

MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://127.0.0.1:27017/')

DATABASE_NAME = 'answers_script'
QUESTIONS_COLLECTION_NAME = 'questions'
CHAT_COLLECTION_NAME = 'chat'
