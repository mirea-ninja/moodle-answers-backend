"""Данный файл является запускатором для сервера"""
from app import sockets, app


if __name__ == "__main__":
    # sockets.run(app, host='0.0.0.0', ssl_context=(
    #     '/var/discourse/shared/standalone/ssl/mirea.ninja.cer', '/var/discourse/shared/standalone/ssl/mirea.ninja.key'))
    sockets.run(app, host='0.0.0.0')
