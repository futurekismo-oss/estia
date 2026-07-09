from player import EstiaPlayer

from threading import Event
from textual import work, on
from textual_thin_slider import ThinSlider
from textual.app import ComposeResult
from textual.widgets import OptionList, Input, Label, Button
from textual.containers import Vertical
from textual.widgets.option_list import Option


class MusicSearch(Vertical):
    player: EstiaPlayer
    label: Label
    is_fetching: bool = False
    dot_count: int = 0

    BINDINGS = [("space", "toggle_pause", "Play/Pause")]

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
            self.update_results_ui, tracks, search_query, search_input
        )

    def update_results_ui(
        self, tracks: list | None, search_query: str, search_input: Input
    ) -> None:
        results_list = self.query_one("#results-list", OptionList)
        results_list.clear_options()
        results_list.visible = True

        if tracks:
            search_input.value = ""
            search_input.placeholder = "Results for: " + search_query
            ui_options = [
                Option(prompt=track["title"], id=track["videoId"]) for track in tracks
            ]
            results_list.add_options(ui_options)
            results_list.highlighted = 0
            results_list.focus()
        else:
            results_list.add_option("No results found.")
            search_input.placeholder = "Search a song"

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search a song", type="text", id="search-bar")
        yield OptionList(id="results-list")
        yield Label("", id="label")
        yield ThinSlider(range_min=0, range_max=100, id="track_progress")
        yield Label("[0:00 / 0:00]", id="playback_time_label")
        yield Button("", variant="warning", id="pause_music_btn")

    def on_mount(self) -> None:
        self.label = self.query_one("#label", Label)
        self.progress_bar = self.query_one("#track_progress", ThinSlider)
        self.stop_playback_work = Event()
        self.playback_time_label = self.query_one("#playback_time_label", Label)
        self.pause_music_btn = self.query_one("#pause_music_btn", Button)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pause_music_btn":
            self.action_toggle_pause()

    def action_toggle_pause(self):
        self.pause_music_btn.label = "" if self.player.player.pause else ""
        self.player.player.pause = not self.player.player.pause

    @on(ThinSlider.Changed, "#track_progress")
    def on_timeline_drag(self, event: ThinSlider.Changed) -> None:
        if event.control.has_focus:
            if not self.is_fetching:
                self.player.player.seek(event.value, reference="absolute-percent")

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

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        song_title = event.option.prompt
        videoId = event.option.id

        if videoId and song_title:
            self.stop_playback_work.set()

            if hasattr(self, "loading_timer"):
                try:
                    self.loading_timer.stop()
                except Exception:
                    pass

            self.progress_bar.value = (  # ty: ignore
                0.0  # Reset progress i play smth before
            )

            self.dot_count = 0
            self.is_fetching = True

            text = f"Fetching {song_title}"
            print(f"Song title: {song_title}")
            self.label.update(text)

            self.loading_timer = self.set_interval(
                0.5, lambda: self.animate_fetcthig(text)
            )

            self.stop_playback_work.clear()
            self.start_playback_worker(videoId, song_title)

        else:
            self.label.update("Selected a placeholder or invalid track.")

    @work(thread=True)  # runs on a different thread
    def start_playback_worker(self, video_id: str, song_title: str) -> None:
        self.player.play_song(video_id)  # so as not the block the main UI loop

        self.player.player.wait_until_playing()

        self.is_fetching = False
        self.app.call_from_thread(self.loading_timer.stop)

        while self.player.player.duration is not None:
            if self.stop_playback_work.is_set():
                self.app.call_from_thread(setattr, self.progress_bar, "value", 0.0)
                break

            total_seconds = self.player.player.duration

            self.app.call_from_thread(setattr, self.pause_music_btn, "visible", True)
            self.app.call_from_thread(
                setattr, self.playback_time_label, "visible", True
            )
            self.app.call_from_thread(setattr, self.progress_bar, "visible", True)

            # The time that has gone by will be the total time minus time remain
            # Basic Math, if there are 5 seconds remaining and the total is 6
            # it becomes 2 / 6 which is correct
            seconds_remaining = total_seconds - self.player.player.time_remaining  # pyright: ignore

            if self.progress_bar:
                percentage = (seconds_remaining / total_seconds) * 100
                self.app.call_from_thread(
                    setattr,
                    self.progress_bar,
                    "value",
                    clamp(percentage, 0.0, 100.0),
                )

            if total_seconds is not None and seconds_remaining is not None:
                total_minutes, total_secs_mod = divmod(int(total_seconds), 60)
                total_time = f"{total_minutes}:{total_secs_mod:02d}"

                minutes_remaining, secs_left_remaining = divmod(
                    int(seconds_remaining), 60
                )
                remaining_time = f"{minutes_remaining}:{secs_left_remaining:02d}"

                self.app.call_from_thread(
                    self.label.update,
                    f"Playing {song_title}",
                )

                self.app.call_from_thread(
                    self.playback_time_label.update,
                    f"[{remaining_time} / {total_time}]",
                )

            # Sleep for a second so as not max out our poor cpu
            from time import sleep

            sleep(1)


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))
