from gzip import compress, decompress
from json import loads, dumps

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
