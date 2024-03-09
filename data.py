from gzip import compress, decompress
from json import loads, dumps
from dotenv import load_dotenv
from os import getcwd, environ
from os.path import join
from datetime import time
import configparser

class Config:
    def __init__(self):
        self.parser = configparser.ConfigParser()
        self.parser.read("config.ini")

        if "gremlinbot" not in self.parser:
            self.parser.add_section("gremlinbot")
    
    def set(self, **kwargs):
        for key in kwargs.keys():
            self.parser.set("gremlinbot", key, str(kwargs[key]))

        with open("config.ini", "w") as file:
            self.parser.write(file)

    def get(self, key, default=None):
        if key in self.parser["gremlinbot"]:
            return self.parser.getint("gremlinbot", key)
        return default

config = Config()

load_dotenv(join(getcwd(), ".env"))

TOKEN = environ.get("TOKEN")
APPLICATION_ID = int(environ.get("APPLICATION_ID"))
CANDIDATES_PER_PAGE = 10
ACCENT = 0x1199ff

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

def add_candidate(message):
    candidates.append({
        "image-url": message.attachments[0].url,
        "author-name": message.author.display_name,
        "author-avatar-url": message.author.display_avatar.url,
        "author-mention": message.author.mention,
        "message-url": message.jump_url,
        "message-id": message.id,
        "description": message.content
    })

    save_data()

    return len(candidates) - 1