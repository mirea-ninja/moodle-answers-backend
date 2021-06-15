from re import DEBUG
from flask import Flask
from flask_socketio import SocketIO
import os
import pymongo
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

client = pymongo.MongoClient('connection-string-here')

database = client['answers_script']

questions_collection = client.get_database(
    'answers_script', read_concern=ReadConcern('majority'),
    write_concern=WriteConcern('majority')).questions

chat_collection = client.get_database(
    'answers_script', read_concern=ReadConcern('majority'),
    write_concern=WriteConcern('majority')).chat

# questions_collection = database['questions']
# chat_collection = database['chat']

app = Flask(__name__)
app.debug = True
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

sockets = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

from . import answers, routes
