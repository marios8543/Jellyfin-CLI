from os.path import isfile
from os import devnull, getenv
from aio_mpv_jsonipc import MPV
from asyncio import get_event_loop, sleep
from datetime import timedelta

def ticks_to_seconds(ticks):
    return int(ticks*(1/10000000))

def seconds_to_ticks(seconds):
    return int(seconds * pow(10, 9) / 100)

class Player:
    def __init__(self, context):
        self.context = context

        self.mpv = None
        self.item = None
        self.position = 0
        self.duration = 0
        self.playing = False
        self.paused = False

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

    
    async def _send_progress(self):
        await self.context.client.post("{}/Sessions/Playing/Progress".format(self.context.url), json={
            "EventName": "timeupdate",
            "ItemId": self.item.id,
            "MediaSourceId": self.item.id,
            "PositionTicks": seconds_to_ticks(self.position)
        })

    async def _progress_loop(self):
        while self.playing:
            await self._send_progress()
            await sleep(10)
    
    async def _update_time(self, time):
        try:
            self.position = int(time)
        except:
            pass

    async def _play(self, item, block=True):
        if self.playing:
            await self.mpv.send(["quit"])
        self.item = item
        self.position = 0
        self.duration = int(ticks_to_seconds(item.ticks))
        self.playing = True
        try:
            key = await self._get_api_key()
        except:
            key = self.context.get_token()
            print("Could not create API token. I will use your login token. Be careful to not leak it!")
        url = "{}/Items/{}/Download?api_key={}".format(self.context.url, item.id, key)
        self.mpv = MPV(media=url)
        await self.mpv.start()
        self.mpv.listen_for("property-change", self._update_time)
        await self.mpv.send(["observe_property", 1, "time-pos"])
        async def _():
            await self.mpv.wait_complete()
            self.playing = False
            await self._delete_api_key(key)
        if block:
            await _()
        else:
            get_event_loop().create_task(_())

    def play(self, button, item):
        get_event_loop().create_task(self._play(item))

    def pause(self):
        if self.paused:
            self.paused = False
            get_event_loop().create_task(self.mpv.send(["set_property", "pause", False]))
        else:
            self.paused = True
            get_event_loop().create_task(self.mpv.send(["set_property", "pause", True]))

    async def stop(self):
        self.playing = False
        try:
            await self.mpv.stop()
        except:
            pass

    def get_playback_string(self):
        position = timedelta(seconds=self.position)
        duration = timedelta(seconds=self.duration)
        return " {}                     {} / {}".format(self.item.name, position, duration)