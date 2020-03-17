from datetime import datetime

class Item:
    def __init__(self, res, context):
        self.id = res["Id"]
        self.name = res["Name"]
        self.is_folder = res["IsFolder"]
        self.played = res["UserData"]["Played"]
        if "RunTimeTicks" in res:
            self.ticks = res["RunTimeTicks"]
        else:
            self.ticks = 9
        self.context = context

    def __str__(self):
        return self.name