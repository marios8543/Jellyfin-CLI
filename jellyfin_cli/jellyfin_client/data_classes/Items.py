from datetime import datetime

class Item:
    def __init__(self, res, context):
        self.id = res["Id"]
        self.name = res["Name"]
        self.is_folder = res["IsFolder"]
        self.played = res["UserData"]["Played"]

        self.context = context

    def __str__(self):
        return self.name