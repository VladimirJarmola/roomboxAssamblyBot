from flask import Flask
from threading import Thread
import random

server = Flask('')

@server.route('/')
def home():
    return 'Bot starting'

def run():
    server.run(
        host='0.0.0.0',
        port=random.randint(2000, 9000)
    )

def keep_alive():
    t = Thread(target=run)
    t.start()
