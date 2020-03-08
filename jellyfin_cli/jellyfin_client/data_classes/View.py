from jellyfin_cli.jellyfin_client.data_classes.Shows import Show
from jellyfin_cli.jellyfin_client.data_classes.Movies import Movie
from jellyfin_cli.jellyfin_client.data_classes.Audio import Song

class HttpError(Exception):
    pass

class View:
    def __init__(self, res, context):
        self.name = res["Name"]
        self.id = res["Id"]
        self.etag = res["Etag"]
        self.parent_id = res["ParentId"]
        if res["CollectionType"] == "movies":
            self.view_type = "Movie"
        elif res["CollectionType"] == "tvshows":
            self.view_type = "Series"
        elif res["CollectionType"] == "music":
            self.view_type = "Audio"
        self.context = context

    def __str__(self):
        return self.name

    async def get_items(self, start=0, limit=100):
        res = await self.context.client.get("{}/Users/{}/Items".format(self.context.url,self.context.user_id), params={
            "SortBy": "DateCreated,SortName,ProductionYear",
            "SortOrder": "Descending",
            "Recursive": "true",
            "Fields": "PrimaryImageAspectRatio%2CMediaSourceCount,BasicSyncInfo",
            "ImageTypeLimit": "1",
            "EnableImageTypes": "Primary%2CBackdrop%2CBanner%2CThumb",
            "StartIndex": start,
            "Limit": limit,
            "ParentId": self.id,
            "IncludeItemTypes": self.view_type
        })
        if res.status == 200:
            res = await res.json()
            r = []
            for i in res["Items"]:
                if i["Type"] == "Movie":
                    r.append(Movie(i, self.context))
                elif i["Type"] == "Audio":
                    r.append(Song(i, self.context))
                elif i["Type"] == "Series":
                    r.append(Show(i, self.context))
            return r
        else:
            raise HttpError(await res.text())

    async def get_latest(self, limit=30):
        #TODO: Implement audio stuff
        if self.view_type == "Audio":
            raise NotImplementedError()
        res = await self.context.client.get("{}/Users/{}/Items/Latest".format(self.context.url, self.context.user_id), params={
            "Limit": limit,
            "ParentId": self.id,
            "Fields": "BasicSyncInfo"
        })
        if res.status == 200:
            res = await res.json()
            r = []
            for i in res:
                if i["Type"] == "Movie":
                    r.append(Movie(i, self.context))
                elif i["Type"] == "Audio":
                    r.append(Song(i, self.context))
                elif i["Type"] == "Series":
                    r.append(Show(i, self.context))
            return r
        else:
            raise HttpError(await res.text())