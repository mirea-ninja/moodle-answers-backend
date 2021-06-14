from re import DEBUG
from flask import Flask
from flask_socketio import SocketIO
import os
import pymongo

client = pymongo.MongoClient('mongodb+srv://msiet5wVdc5fh3AS:msiet5wVdc5fh3AS@schedulebot.xredu.mongodb.net/ScheduleBot?retryWrites=true&w=majority')
database = client['answers_script']
questions_collection = database['questions']
chat_collection = database['chat']

app = Flask(__name__)
app.debug = True
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024

sockets = SocketIO(app, cors_allowed_origins="*")

from . import answers, routes
