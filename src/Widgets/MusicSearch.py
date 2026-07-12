from player import EstiaPlayer
import json

from threading import Event
from textual import work
from textual.app import ComposeResult
from textual.widgets import Input, Label, SelectionList
from textual.widgets.selection_list import Selection
from textual.containers import Vertical
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


class MusicSearch(Vertical):
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
        yield Label("[0:00 / 0:00]", id="playback_time_label")
        # yield Button("", variant="warning", id="pause_music_btn")

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

    # @work(thread=True)  # runs on a different thread
    # def start_playback_worker(self, video_id: str, song_title: str) -> None:
    #     self.player.play_song(video_id)  # so as not the block the main UI loop
    #
    #     self.player.player.wait_until_playing()
    #
    #     self.is_fetching = False
    #     # self.app.call_from_thread(self.loading_timer.stop)
    #
    #     while self.player.player.duration is not None:
    #         if self.stop_playback_work.is_set():
    #             self.app.call_from_thread(setattr, self.progress_bar, "value", 0.0)
    #             break
    #
    #         total_seconds = self.player.player.duration
    #
    #         # self.app.call_from_thread(setattr, self.pause_music_btn, "visible", True)
    #         self.app.call_from_thread(
    #             setattr, self.playback_time_label, "visible", True
    #         )
    #         self.app.call_from_thread(setattr, self.progress_bar, "visible", True)
    #
    #         # The time that has gone by will be the total time minus time remain
    #         # Basic Math, if there are 5 seconds remaining and the total is 6
    #         # it becomes 2 / 6 which is correct
    #         seconds_remaining = total_seconds - self.player.player.time_remaining  # pyright: ignore
    #
    #         if self.progress_bar:
    #             percentage = (seconds_remaining / total_seconds) * 100
    #             self.app.call_from_thread(
    #                 setattr,
    #                 self.progress_bar,
    #                 "value",
    #                 clamp(percentage, 0.0, 100.0),
    #             )
    #
    #         if total_seconds is not None and seconds_remaining is not None:
    #             total_minutes, total_secs_mod = divmod(int(total_seconds), 60)
    #             total_time = f"{total_minutes}:{total_secs_mod:02d}"
    #
    #             minutes_remaining, secs_left_remaining = divmod(
    #                 int(seconds_remaining), 60
    #             )
    #             remaining_time = f"{minutes_remaining}:{secs_left_remaining:02d}"
    #
    #             self.app.call_from_thread(
    #                 self.label.update,
    #                 f"Playing {song_title}",
    #             )
    #
    #             self.app.call_from_thread(
    #                 self.playback_time_label.update,
    #                 f"[{remaining_time} / {total_time}]",
    #             )
    #
    #         # Sleep for a second so as not max out our poor cpu
    #         from time import sleep
    #
    #         sleep(1)

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
