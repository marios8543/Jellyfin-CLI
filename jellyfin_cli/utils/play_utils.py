from asyncio import create_subprocess_exec, get_event_loop
from os.path import isfile
from os import devnull, getenv

class Player:
    def __init__(self, context):
        self.context = context
        self.player_path = getenv("PLAYER_PATH", self.determine_player())

        self.process = None

    def determine_player(self):
        if isfile("/usr/bin/mpv"):
            return "/usr/bin/mpv"
        if isfile("/usr/bin/vlc"):
            return "/usr/bin/vlc"

    async def _get_api_keys(self):
        res = await self.context.client.get("{}/Auth/Keys".format(self.context.url))
        if res.status == 200:
            res = await res.json()
            return {i["AppName"] : i["AccessToken"] for i in res["Items"]}

    async def _get_api_key(self):
        keys = await self._get_api_keys()
        if "jellyfin_cli_play" in keys:
            return keys["jellyfin_cli_play"]
        else:    
            await self.context.client.post("{}/Auth/Keys".format(self.context.url), data={
                "App": "jellyfin_cli_play"
            })
            return await self._get_api_key()

    async def _delete_api_key(self, key=None):
        if not key:
            key = await self._get_api_key()
        await self.context.client.delete("{}/Auth/Keys/{}".format(self.context.url, key))

    async def _play(self, item):
        key = await self._get_api_key()
        url = "{}/Items/{}/Download?api_key={}".format(self.context.url, item.id, key)
        self.process = await create_subprocess_exec(self.player_path , url)
        await self.process.wait()
        await self._delete_api_key(key)
        
    def play(self, button, item):
        get_event_loop().create_task(self._play(item))

    def stop(self):
        self.process.terminate()