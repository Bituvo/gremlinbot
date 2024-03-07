from gzip import compress, decompress
from json import loads, dumps
from dotenv import load_dotenv
from os import getcwd, environ
from os.path import join
from datetime import time

load_dotenv(join(getcwd(), ".env"))

TOKEN = environ.get("TOKEN")
APPLICATION_ID = int(environ.get("APPLICATION_ID"))
BOT_USER_ID = int(environ.get("BOT_USER_ID"))
ROLE_ID = int(environ.get("ROLE_ID"))
GREMLINS_ID = int(environ.get("GREMLINS_ID"))
THREAD_ID = int(environ.get("THREAD_ID"))
CANDIDATES_PER_PAGE = 10
ACCENT = 0x1199ff
NOON_EST = time(hour=17)

def load_data():
    with open("gremlins.dat", "rb") as file:
        return loads(decompress(file.read())).values()
    
def save_data():
    with open("gremlins.dat", "wb") as file:
        file.write(compress(dumps({
            "amount-elected": amount_elected,
            "elected-message-ids": elected_message_ids,
            "candidates": candidates
        }).encode()))

amount_elected, elected_message_ids, candidates = load_data()
