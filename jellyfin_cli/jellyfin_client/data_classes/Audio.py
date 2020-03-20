from jellyfin_cli.jellyfin_client.data_classes.Items import Item

class Audio(Item):
    def __init__(self, res, context):
        super().__init__(res, context)
        self.production_year = res["ProductionYear"] if "ProductionYear" in res else None
        self.artists = res["Artists"] if "Artists" in res else ["Unknown Artist"]
        self.album = res["Album"] if "Album" in res else "Unknown Album"

class Album(Item):
    def __init__(self ,res, context):
        super().__init__(res, context)
        self.artists = res["Artists"]
        self.album_artist = res["AlbumArtist"] if "AlbumArtist" in res and res["AlbumArtist"] else "Unknown Artist"
        self.item_count = res["ChildCount"] if "ChildCount" in res else 0

    async def get_songs(self, sort="SortName"):
        res = await self.context.client.get("{}/Users/{}/Items".format(self.context.url, self.context.user_id), params={
            "ParentId": self.id,
            "Fields": "BasicSyncInfo",
            "SortBy": sort
        })
        if res.status == 200:
            res = await res.json()
            r = []
            for i in res["Items"]:
                r.append(Audio(i, self.context))
            return r