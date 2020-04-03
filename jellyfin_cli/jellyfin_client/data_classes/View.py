from jellyfin_cli.jellyfin_client.data_classes.Shows import Show, Episode
from jellyfin_cli.jellyfin_client.data_classes.Movies import Movie
from jellyfin_cli.jellyfin_client.data_classes.Audio import Album, Audio
from jellyfin_cli.jellyfin_client.data_classes.Items import Playlist

class HttpError(Exception):
    pass

class View:
    def __init__(self, res, context):
        self.name = res["Name"]
        self.id = res["Id"]
        self.etag = res["Etag"]
        self.parent_id = res["ParentId"] if "ParentId" in res else None
        self._fields = "BasicSyncInfo"
        self._recursive = True
        if "CollectionType" not in res:
            self.view_type = "Mixed"
            self._sort = "IsFolder,SortName"
            self._fields = "SortName"
            self._recursive = False
        elif res["CollectionType"] == "movies":
            self._sort = "DateCreated,SortName,ProductionYear"
            self.view_type = "Movie"
        elif res["CollectionType"] == "tvshows":
            self._sort = "DateCreated,SortName,ProductionYear"
            self.view_type = "Series"
        elif res["CollectionType"] == "music":
            self._sort = "DatePlayed"
            self.view_type = "Audio"
        elif res["CollectionType"] == "playlists":
            self._sort = "IsFolder,SortName"
            self.view_type = "Playlist"
        self.context = context

    def __str__(self):
        return self.name

    async def get_items(self, start=0, limit=100, sort=None):
        if not sort:
            sort = self._sort
        params={
            "SortBy": sort,
            "SortOrder": "Descending",
            "Recursive": "true" if self._recursive else "false",
            "Fields": self._fields,
            "StartIndex": start,
            "Limit": limit,
            "ParentId": self.id
        }
        if self.view_type != "Mixed":
            params["IncludeItemTypes"] = self.view_type
        res = await self.context.client.get("{}/Users/{}/Items".format(self.context.url,self.context.user_id), params=params)
        if res.status == 200:
            res = await res.json()
            r = []
            for i in res["Items"]:
                if i["Type"] == "Movie":
                    r.append(Movie(i, self.context))
                elif i["Type"] == "Audio":
                    r.append(Audio(i, self.context))
                elif i["Type"] == "Series":
                    r.append(Show(i, self.context))
                elif i["Type"] == "MusicAlbum":
                    r.append(Album(i, self.context))
                elif i["Type"] == "Episode":
                    r.append(Episode(i, self.context))
            return r
        else:
            raise HttpError(await res.text())

    async def get_latest(self, limit=30):
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
                    r.append(Audio(i, self.context))
                elif i["Type"] == "Series":
                    r.append(Show(i, self.context))
                elif i["Type"] == "MusicAlbum":
                    r.append(Album(i, self.context))
                elif i["Type"] == "Episode":
                    r.append(Episode(i, self.context))
            return r
        else:
            raise HttpError(await res.text())