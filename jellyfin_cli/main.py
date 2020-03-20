from jellyfin_cli.utils.login_helper import login
from jellyfin_cli.utils.play_utils import Player
from asyncio import get_event_loop, sleep
from jellyfin_cli.urwid_overrides.Button import ButtonNoArrows as Button
import urwid

def calculate_percentage(rows, prcnt):
    return int((rows/100)*prcnt)

PALLETE = [
    ('bg', 'black', 'light gray'),
    ('bg_inverted', 'white', 'light gray')
]

class App:
    def __init__(self):
        self.loop = get_event_loop()
        self.client = self.loop.run_until_complete(login())
        self.player = Player(self.client.context)
        self.widgets = [urwid.Text("Logged in as {}".format(self.client.context.username)), urwid.Divider(bottom=1)]
        self.draw = urwid.MainLoop(urwid.Filler(urwid.Pile([])), palette=PALLETE, event_loop=urwid.AsyncioEventLoop(loop=self.loop))
        self.previous_key_callback = (None, (None))
        self.draw.unhandled_input = self._process_keypress

        self._last_view = self.draw_search
        self.search_query = ""
        self.search_edit = urwid.Edit("Enter your search query...", edit_text=self.search_query)

    def _process_keypress(self, key):
        if key == "tab":
            try:
                if self.previous_key_callback[1]:
                    self.previous_key_callback[0](*self.previous_key_callback[1])
                else:
                    self.previous_key_callback[0]()
            except:
                pass
        elif key == "s":
            self.draw_search(None, "")
        elif key == "p":
            if self.player.playing:
                self.player.pause()
        elif key == "q":
            raise urwid.ExitMainLoop()

    def _draw_table(self, items, title=None, prcnt=30, callback=None):
        if not callback:
            callback = self.play
        rows = calculate_percentage(self.draw.screen.get_cols_rows()[1], prcnt)
        texts = [Button(str(i), on_press=callback(i) if not hasattr(self, callback.__name__) else callback, user_data=i) for i in items]
        widgets = [urwid.Text(("bg", title), align=urwid.CENTER)] if title else []
        widgets.append(urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(texts)), rows))
        return widgets

    def _draw_screen(self):
        self.draw.widget.body = urwid.Pile(self.widgets)
    
    def _empty_screen(self, text=""):
        self.draw.widget.body = urwid.Text(text)

    def _clear_widgets(self):
        self.widgets = [urwid.Text("Logged in as {}".format(self.client.context.username)), urwid.Divider(bottom=1)]

    def _clear_search(self):
        self.search_query = ""
        self.search_edit = urwid.Edit()
        
    def _add_widget(self, wd):
        if type(wd) == list:
            self.widgets.extend(wd)
        else:
            self.widgets.append(wd)
        self.widgets.append(urwid.Divider(div_char="_", top=1, bottom=1))
        self.draw.widget.body = urwid.Pile(self.widgets)

    async def _draw_home(self):
        self.widgets = [urwid.Text("Logged in as {}".format(self.client.context.username)), urwid.Divider(bottom=1)]
        views = await self.client.get_views()
        columns = urwid.Columns([Button(("bg", i.name), on_press=self.draw_view, user_data=i) for i in views])
        self._add_widget(columns)
        resume = await self.client.get_resume()
        nextup = await self.client.get_nextup()
        self._add_widget(self._draw_table(resume,"Continue Watching", prcnt=30))
        self._add_widget(self._draw_table(nextup, "Next Up", prcnt=28))
        self._add_widget(urwid.Text("Tab: Go back | s: Search | p: Play/Pause | q: Exit"))
        self.previous_key_callback = (None, None)

    def draw_home(self):
        self.loop.create_task(self._draw_home())

    async def _draw_view(self, view):
        self._clear_widgets()
        if view.view_type == "Audio":
            await self._draw_audio(view)
        elif view.view_type == "Playlist":
            self._last_view = view
            items = await view.get_items()
            self._add_widget(self._draw_table(items, view.name, prcnt=98, callback=self.draw_playlist))
        else:
            items = await view.get_items(limit=500)
            if view.view_type == "Series":
                callback = self.draw_seasons
            else:
                callback = None
            self._add_widget(self._draw_table(items, str(view), prcnt=96, callback=callback))
            self._last_view = view
        self.previous_key_callback = (self.draw_home, None)

    def draw_view(self, b, view):
        self.loop.create_task(self._draw_view(view))

    async def _draw_playlist(self, playlist):
        items = await playlist.get_items()
        callbacks = {"Movie":self.play, "Episode": self.play, "Audio": self.play_bg}
        self._clear_widgets()
        self._add_widget(self._draw_table(items, playlist.name, prcnt=98, callback=lambda i: callbacks[i.__class__.__name__]))
        self.previous_key_callback = (self.draw_view, (None, self._last_view))
    
    def draw_playlist(self, b, playlist):
        self.loop.create_task(self._draw_playlist(playlist))

    async def _draw_audio(self, view):
        latest = await view.get_latest(limit=16)
        recent = await view.get_items()
        frequent = await view.get_items(sort="PlayCount", limit=8)
        self._add_widget(self._draw_table(latest, title="Latest Music", callback=self.draw_album, prcnt=15))
        self._add_widget(self._draw_table(recent, title="Recently Played", callback=self.play_bg, prcnt=40))
        self._add_widget(self._draw_table(frequent, title="Frequently Played", callback=self.play_bg, prcnt=15))
        self._last_view = view
        self.previous_key_callback = (self.draw_home, None)
    
    async def _draw_album(self, album):
        items = await album.get_songs()
        self._clear_widgets()
        self._add_widget(self._draw_table(items, title=album.name, prcnt=97, callback=self.play_bg))
        self.previous_key_callback = (self.draw_view, (None, self._last_view))

    def draw_album(self, b, album):
        self.loop.create_task(self._draw_album(album))

    async def _draw_seasons(self, series):
        seasons = await series.get_seasons()
        self._clear_widgets()
        self._add_widget(self._draw_table(seasons, str(series), prcnt=96, callback=self.draw_episodes))
        self.previous_key_callback = (self.draw_view, (None, self._last_view))

    def draw_seasons(self, b, series, callback=None):
        self.loop.create_task(self._draw_seasons(series))

    async def _draw_episodes(self, season):
        episodes = await season.get_episodes()
        self._clear_widgets()
        self._add_widget(self._draw_table(episodes, "{} - {}".format(season.show, season), prcnt=96))
        self.previous_key_callback = (self.draw_seasons, (None, season.show))

    def draw_episodes(self, b, season):
        self.loop.create_task(self._draw_episodes(season))

    async def _draw_search(self):
        self._clear_widgets()
        if len(self.search_query) > 0:
            movies = await self.client.search(self.search_query, "Movie")
            shows = await self.client.search(self.search_query, "Series")
            episodes = await self.client.search(self.search_query, "Episode")
            songs = await self.client.search(self.search_query, "Audio")
            albums = await self.client.search(self.search_query, "MusicAlbum")
            self._add_widget(self.search_edit)
            if movies:
                self._add_widget(self._draw_table(movies, "Movies", callback=self.play, prcnt=20))
            if shows:
                self._add_widget(self._draw_table(shows, "Shows", callback=self.draw_seasons, prcnt=20))
            if episodes:
                self._add_widget(self._draw_table(episodes, "Episodes", callback=self.play, prcnt=20))
            if songs:
                self._add_widget(self._draw_table(songs, "Songs", callback=self.play_bg, prcnt=20))
            if albums:
                self._add_widget(self._draw_table(albums, "Albums", callback=self.draw_album, prcnt=20))
        else:
            urwid.connect_signal(self.search_edit, "change", self.draw_search)
            recommended = await self.client.get_recommended()
            self._add_widget(self.search_edit)
            callbacks = {"Movie":self.play, "Show": self.draw_seasons, "Episode": self.play}
            self._add_widget(self._draw_table(recommended, "Suggestions", prcnt=96, callback=lambda i: callbacks[i.__class__.__name__]))
        self.previous_key_callback = (lambda: [self.draw_home(), urwid.disconnect_signal(self.search_edit, "change", self.draw_search), self._clear_search()], (None))

    def draw_search(self, e, text):
        self.search_query = text
        self.loop.create_task(self._draw_search())

    async def _play(self, item):
        self._empty_screen()
        await self.player._play(item)
        self._draw_screen()

    async def _bg_play(self , item):
        await self.player._play(item, block=False)
        while self.player.playing:
            play_string = self.player.get_playback_string()
            if not self.previous_key_callback[0]:
                try:
                    self.draw.widget.body.contents[-2][0].set_text(play_string)
                    self.draw.draw_screen()
                except:
                    break
            await sleep(1)
    
    def play(self, b, item, bg=False):
        if bg:
            self.loop.create_task(self._bg_play(item))
        else:
            self.loop.create_task(self._play(item))

    def play_bg(self, b, item):
        self.play(b, item, bg=True)

    def _run(self):
        self.draw_home()
        self.draw.run()

    def __call__(self):
        return self._run()

app = App()
if __name__ == "__main__":
    app()