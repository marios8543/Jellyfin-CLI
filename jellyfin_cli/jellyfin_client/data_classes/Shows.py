from jellyfin_cli.jellyfin_client.data_classes.Items import Item

class Show(Item):
    def __init__(self, res, context):
        super().__init__(res, context)
    
    async def get_seasons(self):
        res = await self.context.client.get("{}/Shows/{}/Seasons".format(self.context.url, self.id),params={
            "userId": self.context.user_id
        })
        if res.status == 200:
            res = await res.json()
            return [Season(i, self) for i in res["Items"]]
        else:
            from jellyfin_cli.jellyfin_client.JellyfinClient import HttpError
            raise HttpError(await res.text())

class Season(Item):
    def __init__(self, res, show):
        super().__init__(res, show.context)
        if "IndexNumber" in res:
            self.index = res["IndexNumber"]
        else:
            self.index = 0
        self.is_folder = res["IsFolder"]
        self.show = show
    
    def __str__(self):
        return self.name

    async def get_episodes(self):
        res = await self.context.client.get("{}/Shows/{}/Episodes".format(self.context.url, self.show.id), params={
            "seasonId": self.id,
            "userId": self.context.user_id
        })
        if res.status == 200:
            res = await res.json()
            return [Episode(i, self.context) for i in res["Items"]]
        else:
            from jellyfin_cli.jellyfin_client.JellyfinClient import HttpError
            raise HttpError(await res.text())

class Episode(Item):
    def __init__(self, res, context):
        super().__init__(res, context)
        self.subbed = res["HasSubtitles"] if "HasSubtitles" in res else False

        self.context = context

    def __str__(self):
        return "{} {}".format(self.name, "[Subtitled]" if self.subbed else "")