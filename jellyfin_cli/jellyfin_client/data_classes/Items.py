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

class Playlist(Item):
    def __init__(self, res, context):
        super().__init__(res, context)

    async def get_items(self):
        res = await self.context.client.get("{}/Playlists/{}/Items".format(self.context.url, self.id), params={
            "Fields": "BasicSyncInfo",
            "UserId": self.context.user_id
        })
        if res.status == 200:
            res = await res.json()
            r = []
            from jellyfin_cli.jellyfin_client.data_classes.Audio import Audio
            from jellyfin_cli.jellyfin_client.data_classes.Shows import Episode
            from jellyfin_cli.jellyfin_client.data_classes.Movies import Movie
            for i in res["Items"]:
                if i["Type"] == "Audio":
                    r.append(Audio(i, self.context))
                elif i["Type"] == "Episode":
                    r.append(Episode(i, self.context))
                elif i["Type"] == "Movie":
                    r.append(Movie(i, self.context))
            return r
        else:
            from jellyfin_cli.jellyfin_client.JellyfinClient import HttpError
            raise HttpError(await res.text())