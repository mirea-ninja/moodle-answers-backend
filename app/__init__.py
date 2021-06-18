import asyncio
from aiohttp import web
import socketio
import pymongo

client = pymongo.MongoClient('mongodb://127.0.0.1:27017')

database = client['answers_script']
questions_collection = database['questions']
chat_collection = database['chat']

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

from . import answers, routes
