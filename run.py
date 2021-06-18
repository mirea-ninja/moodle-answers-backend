"""Данный файл является запускатором для сервера"""
from app import app, web
import ssl


if __name__ == "__main__":
    # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    # ssl_context.load_cert_chain('/var/discourse/shared/standalone/ssl/mirea.ninja.cer', '/var/discourse/shared/standalone/ssl/mirea.ninja.key')
    # web.run_app(app, ssl_context=ssl_context)
    web.run_app(app, port=5000)
