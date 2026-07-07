import db
from player import EstiaPlayer
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList, Input, Label
from textual.containers import Vertical
from textual.widgets.option_list import Option


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


class MusicSearch(Vertical):
    player: EstiaPlayer

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search a song", type="text", id="search-bar")
        yield OptionList(id="results-list")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-bar":
            search_query = event.value.strip()  # Remove spaces redunant spaces
            if not search_query:
                return

            event.input.placeholder = "Searching..."
            event.input.value = ""

            tracks = self.player.search_songs(search_query)  # Search for the song

            results_list = self.query_one("#results-list", OptionList)
            results_list.clear_options()  # Safety: remove anything in results

            if tracks:
                event.input.value = ""
                event.input.placeholder = "Results for: " + search_query
                ui_options = [
                    Option(
                        prompt=track["title"], id=track["videoId"]
                    )  # for each of the track in tracks make a Option element and
                    # append botht the track title and video id to it
                    for track in tracks
                ]

                results_list.add_options(ui_options)

                results_list.highlighted = 0

                results_list.focus()
            else:
                results_list.add_option("No results found.")
                event.input.placeholder = "Search a song"

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        song_title = event.option.prompt
        videoId = event.option.id
        label = self.app.query_one(Label)

        if videoId:
            self.dot_count = 0

            def animate_dots():
                self.dot_count = (self.dot_count % 3) + 1
                dots = "." * self.dot_count

                label.update(f"Fetching {song_title}{dots}")

            self.loading_timer = self.set_interval(0.5, animate_dots)

            self.start_playback_worker(videoId, song_title)

        else:
            label.update("Selected a placeholder or invalid track.")

    @work(thread=True)  # runs on a different thread
    def start_playback_worker(self, video_id: str, song_title: str) -> None:
        self.player.play_song(video_id)  # so as not the block the main UI loop

        self.player.player.wait_until_playing()

        self.app.call_from_thread(self.loading_timer.stop)

        self.app.call_from_thread(
            self.app.query_one(Label).update, f"Playing {song_title}"
        )


class EstiaApp(App):
    TITLE = "Estia"

    CSS_PATH = "estai.tcss"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()

    def compose(self) -> ComposeResult:
        self.music = EstiaPlayer()

        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        search_widget = MusicSearch()
        search_widget.player = self.music

        yield search_widget
        yield Label("Nothing has been selected yet")
        yield Footer()


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
