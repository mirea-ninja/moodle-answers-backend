"""Данный файл является запускатором для сервера"""
from app import sockets, app


if __name__ == "__main__":
    # sockets.run(app, debug=False, host='0.0.0.0', certfile='path_here', keyfile='path_here')
    sockets.run(app, host='0.0.0.0')
