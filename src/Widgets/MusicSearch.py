from player import EstiaPlayer


from textual import work
from textual.app import ComposeResult
from textual.widgets import OptionList, Input, Label
from textual.containers import Vertical
from textual.widgets.option_list import Option


class MusicSearch(Vertical):
    player: EstiaPlayer
    label: Label
    is_fetching: bool = False
    dot_count: int = 0

    @work(thread=True)  # <- Works on another thread
    def thread_safe_search_song(self, search_query: str, search_input: Input) -> None:
        # ↓ Used to catch no internet errors
        from requests.exceptions import ConnectionError as requestsConnectionError

        try:
            tracks = self.player.search_songs(search_query)
        except requestsConnectionError:
            tracks = None
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

    def on_mount(self) -> None:
        self.label = self.app.query_one(Label)

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

        if videoId:
            self.dot_count = 0
            self.is_fetching = True

            text = f"Fetching {song_title}"
            self.label.update(text)

            self.loading_timer = self.set_interval(
                0.5, lambda: self.animate_fetcthig(text)
            )

            self.start_playback_worker(videoId, song_title)

        else:
            self.label.update("Selected a placeholder or invalid track.")

    @work(thread=True)  # runs on a different thread
    def start_playback_worker(self, video_id: str, song_title: str) -> None:
        self.player.play_song(video_id)  # so as not the block the main UI loop

        self.player.player.wait_until_playing()

        self.is_fetching = False

        self.app.call_from_thread(self.loading_timer.stop)

        self.app.call_from_thread(
            self.app.query_one(Label).update, f"Playing {song_title}"
        )
