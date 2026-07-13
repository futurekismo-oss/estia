import db
import sys
import os
import json
from player import EstiaPlayer

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, Static
from textual import work, events, on
from textual.css.query import NoMatches
import contextlib


# === Widgets ===
from Widgets.Pomodoro import Pomodoro
from Widgets.MusicSearch import MusicSearch, ResultsList
from Widgets.Playlist import Playlist


if hasattr(sys, "nuitka_srcdir"):
    os.environ["MPV_LD_LIBRARY_PATH"] = sys.nuitka_srcdir


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


# === Main App ===
class EstiaApp(App):
    was_mouse_down_on_playlist: bool = False
    songs_to_drop: list[str] = []

    TITLE = "Estia"

    CSS_PATH = "estai.tcss"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()
        self.zone = self.app.query_one("#playlist_list", ListView)
        self.playlist_instance = self.app.query_one(Playlist)

    def compose(self) -> ComposeResult:

        self.music = EstiaPlayer(self)

        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        yield Pomodoro()

        search_widget = MusicSearch()
        search_widget.player = self.music

        yield search_widget

        yield Playlist(id="playlist")
        yield Footer()

    @on(events.MouseDown)
    def on_mouse_down_on_playlist(self, event: events.MouseDown) -> None:

        if (
            (self.screen.get_widget_at(event.screen_x, event.screen_y)[0]).id
            == "results_list"
        ):
            self.was_mouse_down_on_playlist = True

    @on(events.MouseUp)
    @work
    async def on_mouse_up_on_anything(self, event: events.MouseUp) -> None:
        self.was_mouse_down_on_playlist = False

        with contextlib.suppress(NoMatches):
            await self.query_one("#popup", Static).remove()
        # forced to do this, because popup doesn't actually get removed asap, im not sure why
        self.call_after_refresh(self.handle_drop, event)  # <- I'll do it later

    def handle_drop(self, event: events.MouseUp) -> None:

        if (
            self.screen.get_widget_at(event.screen_x, event.screen_y)[0].id
            == "playlist_list"
        ):
            playlist = self.app.query_one("#results_list", ResultsList)
            result_list = self.app.query_one("#playlist", Playlist)
            for tracks in playlist.selected:
                track_data = json.loads(tracks)

                result_list.add_track_safely(track_data["title"], track_data["videoId"])
            playlist.deselect_all()

    @on(events.MouseMove)
    @work
    async def on_mouse_move(self, event: events.MouseMove) -> None:
        if self.was_mouse_down_on_playlist:
            if not self.query("#popup"):
                playlist = self.app.query_one("#results_list", ResultsList)
                await self.mount(
                    popup := Static(f"{len(playlist.selected)} songs", id="popup")
                )
                self.songs_to_drop = playlist.selected
            else:
                popup = self.query_one("#popup", Static)
            popup.offset = (event.screen_x, event.screen_y)


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
