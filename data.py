from gzip import compress, decompress
from json import loads, dumps
from dotenv import load_dotenv
from os import getcwd, environ
from os.path import join
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
            "day-count": day_count,
            "elected-attachment-ids": elected_attachment_ids,
            "candidates": candidates
        }).encode()))

day_count, elected_attachment_ids, candidates = load_data()

def is_eligible(message):
    if message.attachments:
        if not all("image" in attachment.content_type or "video" in attachment.content_type for attachment in message.attachments):
            return False, "An attached gremlin was not found in this post."
    else:
        return False, "An attached gremlin was not found in this post."

    if any(candidate["message-id"] == message.id for candidate in candidates):
        if len(message.attachments) > 1:
            return False, "These gremlins are already in the list of candidates."
        return False, "This gremlin is already in the list of candidates."

    if any(attachment.id in elected_attachment_ids for attachment in message.attachments):
        if len(message.attachments) > 1:
            return False, "These gremlins have already been elected."
        return False, "This gremlin has already been elected."
    
    return True, ""

def add_candidate(message):
    indexes = []
    for attachment in message.attachments:
        candidates.append({
            "attachment-url": attachment.url,
            "attachment-id": attachment.id,
            "filename": attachment.filename,
            "author-name": message.author.display_name,
            "author-mention": message.author.mention,
            "message-url": message.jump_url,
            "message-id": message.id,
            "description": message.content
        })
        indexes.append(len(candidates) - 1)

    save_data()
    return indexes