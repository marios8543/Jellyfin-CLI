from jellyfin_cli.utils.login_helper import login
from jellyfin_cli.utils.play_utils import Player
from asyncio import get_event_loop
from concurrent.futures import ThreadPoolExecutor
import urwid
from jellyfin_cli.urwid_overrides.Button import ButtonNoArrows as Button

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

    def _draw_table(self, items, title, prcnt=30, callback=None):
        if not callback:
            callback = self.play
        rows = calculate_percentage(self.draw.screen.get_cols_rows()[1], prcnt)
        texts = [Button(str(i), on_press=callback, user_data=i) for i in items]
        widgets = [
            urwid.Text(("bg", title), align=urwid.CENTER),
            urwid.BoxAdapter(urwid.ListBox(urwid.SimpleFocusListWalker(texts)), rows)
        ]
        return widgets

    def _draw_screen(self):
        self.draw.widget.body = urwid.Pile(self.widgets)
    
    def _empty_screen(self):
        self.draw.widget.body = urwid.Text("")
        
    def _add_widget(self, wd):
        if type(wd) == list:
            self.widgets.extend(wd)
        else:
            self.widgets.append(wd)
        self.widgets.append(urwid.Divider(div_char="_", top=1, bottom=1))
        self.draw.widget.body = urwid.Pile(self.widgets)

    async def _add_views(self):
        views = await self.client.get_views()
        columns = urwid.Columns([Button(("bg", i.name), on_press=self.draw_view, user_data=i) for i in views])
        self._add_widget(columns)

    async def _add_tables(self):
        resume = await self.client.get_resume()
        nextup = await self.client.get_nextup()
        self._add_widget(self._draw_table(resume,"Continue Watching"))
        self._add_widget(self._draw_table(nextup, "Next Up"))

    async def _draw_view(self, view):
        items = await view.get_items(limit=500)
        self.widgets = []
        if view.view_type == "Series":
            callback = self.draw_seasons
        else:
            callback = None
        self._add_widget(self._draw_table(items, str(view), prcnt=98, callback=callback))

    def draw_view(self, b, view):
        self.loop.create_task(self._draw_view(view))

    async def _draw_seasons(self, series):
        seasons = await series.get_seasons()
        self.widgets = []
        self._add_widget(self._draw_table(seasons, str(series), prcnt=98, callback=self.draw_episodes))

    def draw_seasons(self, b, series):
        self.loop.create_task(self._draw_seasons(series))

    async def _draw_episodes(self, season):
        episodes = await season.get_episodes()
        self.widgets = []
        self._add_widget(self._draw_table(episodes, "{} - {}".format(season.show, season), prcnt=98))

    def draw_episodes(self, b, season):
        self.loop.create_task(self._draw_episodes(season))

    async def _play(self, item):
        self._empty_screen()
        await self.player._play(item)
        await self.render_home()
    
    def play(self, b, item):
        self.loop.create_task(self._play(item))

    async def render_home(self):
        self.widgets = [urwid.Text("Logged in as {}".format(self.client.context.username)), urwid.Divider(bottom=1)]
        await self._add_views()
        await self._add_tables()

    def _run(self):
        self.loop.create_task(self.render_home())
        self.draw.run()

    def __call__(self):
        return self._run()

app = App()
if __name__ == "__main__":
    app()