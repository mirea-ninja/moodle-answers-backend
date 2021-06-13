"""Данный файл является запускатором для сервера"""
from app import sockets, app


if __name__ == "__main__":
    sockets.run(app)
