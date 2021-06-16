from flask import Flask
from flask_socketio import SocketIO
import pymongo

client = pymongo.MongoClient('connection-string-here')

database = client['answers_script']
questions_collection = database['questions']
chat_collection = database['chat']

app = Flask(__name__)
app.debug = True
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

sockets = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

from . import answers, routes
