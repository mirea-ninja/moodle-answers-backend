from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGODB_URL
from .database import db
import socketio


db.client = AsyncIOMotorClient(MONGODB_URL)

sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

from . import answers, routes
