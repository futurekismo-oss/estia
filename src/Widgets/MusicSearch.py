from player import EstiaPlayer
import json

from threading import Event
from textual import work
from textual.app import ComposeResult
from textual.widgets import Input, Label, SelectionList, Button
from textual.widgets.selection_list import Selection
from textual.containers import VerticalScroll
from Widgets.Playlist import Playlist


class ResultsList(SelectionList):
    def compose(self) -> ComposeResult:

        yield SelectionList(id="playlist")

    def update_results_ui(
        self, tracks: list | None, search_query: str, search_input: Input
    ) -> None:
        self.clear_options()
        self.visible = True

        if tracks:
            search_input.value = ""
            search_input.placeholder = "Results for: " + search_query
            ui_options = [
                Selection(
                    prompt=track["title"],
                    id=track["videoId"],
                    value=json.dumps(
                        {"title": track["title"], "videoId": track["videoId"]}
                    ),
                )
                for track in tracks
            ]
            self.add_options(ui_options)
            self.highlighted = 0
            self.focus()
        else:
            search_input.placeholder = "Search a song"


class MusicSearch(VerticalScroll):
    player: EstiaPlayer
    label: Label
    is_fetching: bool = False
    dot_count: int = 0

    def on_mount(self) -> None:
        self.label = self.query_one("#label", Label)
        self.playlist_instance = self.app.query_one(Playlist)
        self.results_list = self.app.query_one("#results_list", ResultsList)

        self.stop_playback_work = Event()

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search a song", type="text", id="search-bar")
        yield ResultsList(id="results_list")
        yield Label("", id="label")

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "playlist_save":
            self.playlist_instance.save_playlist_to_file()
        elif button_id == "playlist_load":
            self.playlist_instance.load_playlist_from_file()

    def animate_fetcthig(self, base_str: str) -> None:
        if not self.is_fetching:
            return
        self.dot_count = (self.dot_count % 3) + 1
        dots = "." * self.dot_count
        self.label.update(f"{base_str}{dots}")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-bar":
            search_query = event.value.strip()  # Remove spaces redunant spaces
            if not search_query:
                return

            self.notify(f"Searching for {search_query}")

            self.thread_safe_search_song(search_query, event.input)

    @work(thread=True)  # <- Works on another thread
    def thread_safe_search_song(self, search_query: str, search_input: Input) -> None:
        # ↓ Used to catch no internet errors
        from requests.exceptions import ConnectionError as requestsConnectionError

        try:
            tracks = self.player.search_songs(search_query)
        except requestsConnectionError:
            self.app.call_from_thread(self.label.update, "Fetching Failed")
            self.app.call_from_thread(
                self.app.notify,
                title="Fetching Failed",
                timeout=5,
                severity="error",
                message="This app requires an internet connection to work, as it streams songs directly from youtube music. However, an offline mode is in the works",
            )
            return

        self.app.call_from_thread(
            self.results_list.update_results_ui, tracks, search_query, search_input
        )


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))
