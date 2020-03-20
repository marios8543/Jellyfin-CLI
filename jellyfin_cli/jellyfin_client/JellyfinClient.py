from aiohttp import ClientSession
from jellyfin_cli.jellyfin_client.data_classes.View import View
from jellyfin_cli.jellyfin_client.data_classes.Shows import Episode, Show
from jellyfin_cli.jellyfin_client.data_classes.Movies import Movie
from jellyfin_cli.jellyfin_client.data_classes.Audio import Audio, Album

class InvalidCredentialsError(Exception):
    def __init__(self):
        Exception("Invalid username, password or server URL")

class HttpError(Exception):
    def __init__(self, text):
        Exception("Something went wrong: {}".format(text))

class ServerContext:
    def __init__(self, res=None, url=None, client=None, cfg=None, username=None):
        if cfg:
            self.url = cfg["url"]
            self.user_id = cfg["user_id"]
            self.server_id = cfg["server_id"]
            self.client = ClientSession(headers={
                "x-emby-authorization": cfg["auth_header"]
            })
            self.username = cfg["username"]
        else:
            self.url = url
            self.user_id = res["User"]["Id"]
            self.server_id = res["ServerId"]
            self.username = username
            self.client = client
    
    def get_token(self):
        header = self.client._default_headers["x-emby-authorization"]
        header = [i.split("=") for i in header.split(",")]
        pairs = {k[0].strip().replace('"',""):k[1].strip().replace('"',"") for k in header}
        return pairs["Token"]

class HttpClient:
    def __init__(self, server, context=None):
        self.client = ClientSession()
        self.server = server
        self.context = context

    async def login(self, username, password):
        try:
            res = await self.client.post(self.server+'/Users/authenticatebyname',data={
                "Username": username,
                "Pw": password
            }, headers={
                "x-emby-authorization":'MediaBrowser Client="Jellyfin CLI", Device="Jellyfin-CLI", DeviceId="None", Version="10.4.3"'
            })
        except Exception:
            raise InvalidCredentialsError()
        if res.status == 200:
            res = await res.json()
            token = res["AccessToken"]
            self.client = ClientSession(headers={
                "x-emby-authorization":'MediaBrowser Client="Jellyfin CLI", Device="Jellyfin-CLI", DeviceId="None", Version="10.4.3", Token="{}"'.format(token)
            })
            self.context = ServerContext(res, self.server, self.client, username=username)
            from jellyfin_cli.utils.login_helper import store_creds
            store_creds(self.context)
            return True
        elif res.status == 401:
            raise InvalidCredentialsError()
        else:
            raise HttpError(await res.text())
    
    async def get_views(self):
        res = await self.context.client.get("{}/Users/{}/Views".format(self.context.url, self.context.user_id))
        if res.status == 200:
            res = await res.json()
            return [View(i, self.context) for i in res["Items"]]
        else:
            raise HttpError(await res.text())

    async def get_resume(self, limit=12, types="Video"):
        res = await self.context.client.get("{}/Users/{}/Items/Resume".format(self.context.url, self.context.user_id), params={
            "Limit": limit,
            "Recursive": "true",
            "Fields": "BasicSyncInfo",
            "MediaTypes": types
        })
        if res.status == 200:
            res = await res.json()
            return [Episode(r, self.context) for r in res["Items"]]
        else:
            raise HttpError(await res.text())

    async def get_nextup(self, limit=24):
        res = await self.context.client.get("{}/Shows/NextUp".format(self.context.url), params={
            "UserId": self.context.user_id,
            "Limit": limit,
            "Recursive": "true",
            "Fields": "BasicSyncInfo"
        })
        if res.status == 200:
            res = await res.json()
            return [Episode(r, self.context) for r in res["Items"]]
        else:
            raise HttpError(await res.text())

    async def search(self, query, media_type, limit=30):
        res = await self.context.client.get("{}/Users/{}/Items".format(self.context.url, self.context.user_id), params={
            "searchTerm": query,
            "IncludeItemTypes": media_type,
            "IncludeMedia": "true",
            "IncludePeople": "false",
            "IncludeGenres": "false",
            "IncludeStudios": "false",
            "IncludeArtists": "false",
            "Fields": "BasicSyncInfo",
            "Recursive": "true",
            "Limit": limit
        })
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
                elif i["Type"] == "Episode":
                    r.append(Episode(i, self.context))
                elif i["Type"] == "MusicAlbum":
                    r.append(Album(i, self.context))
            return r
        else:
            raise HttpError(await res.text())

    async def get_recommended(self, limit=30):
        res = await self.context.client.get("{}/Users/{}/Items".format(self.context.url, self.context.user_id), params={
            "SortBy": "IsFavoriteOrLiked,Random",
            "IncludeItemTypes": "Movie,Series",
            "Recursive": "true",
            "Limit": limit
        })
        if res.status == 200:
            res = await res.json()
            r = []
            for i in res["Items"]:
                if i["Type"] == "Movie":
                    r.append(Movie(i, self.context))
                elif i["Type"] == "Series":
                    r.append(Show(i, self.context))
            return r
        else:
            raise HttpError(await res.text())