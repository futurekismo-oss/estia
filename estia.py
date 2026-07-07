import db
from player import EstiaPlayer

from textual.reactive import reactive
from textual.getters import query_one
from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Button, Digits, Header, Footer, OptionList, Input, Label
from textual.containers import Horizontal, Vertical
from textual.widgets.option_list import Option


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


def animate_dots(
    text: str,
    label: Label,
    count=3,
):
    dot_count = 0
    dot_count = (dot_count % count) + 1
    dots = "." * dot_count

    label.update(f"{text}{dots}")


# === Widgets ===


class Pomodoro(Vertical):
    set_minutes = 0.1  # minutes
    time = reactive(set_minutes * 60)  # 20 Seconds for now

    digits: Digits = query_one("#time", Digits)  # pyright: ignore

    def on_mount(self) -> None:
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self):
        self.time -= 1 / 60
        if self.time <= 0:
            self.time = self.set_minutes * 60
            self.remove_class("started")
            self.update_timer.pause()

    def watch_time(self):
        minutes, seconds = divmod(self.time, 60)
        text = f"{minutes:02.0f}:{seconds:02.0f}"
        self.digits.update(text)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Digits("25:00", id="time")
            with Horizontal():
                yield Button("", variant="success", id="start")
                yield Button("", id="stop", variant="error")
                yield Button("Take a break", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "start":
            self.add_class("started")
            self.update_timer.resume()
        elif button_id == "stop":
            self.remove_class("started")
            self.update_timer.pause()


class MusicSearch(Vertical):
    player: EstiaPlayer
    label: Label

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search a song", type="text", id="search-bar")
        yield OptionList(id="results-list")
        self.label = self.app.query_one(Label)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-bar":
            search_query = event.value.strip()  # Remove spaces redunant spaces
            if not search_query:
                return

            self.label.update(f"Searching for {search_query}")

            try:
                tracks = self.player.search_songs(search_query)  # Search for the song
            except ConnectionError:  # <- Doesnt work for some reason FIX
                tracks = None
                self.app.notify(
                    "THis app requires internet to work, i'll add an offline mode later"
                )

            results_list = self.query_one("#results-list", OptionList)
            results_list.clear_options()  # Safety: remove anything in results

            results_list.visible = True

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

        if videoId:
            self.dot_count = 0

            text = f"Fetching {song_title}"

            self.loading_timer = self.set_interval(0.5, animate_dots(text, self.label))

            self.start_playback_worker(videoId, song_title)

        else:
            self.label.update("Selected a placeholder or invalid track.")

    @work(thread=True)  # runs on a different thread
    def start_playback_worker(self, video_id: str, song_title: str) -> None:
        self.player.play_song(video_id)  # so as not the block the main UI loop

        self.player.player.wait_until_playing()

        self.app.call_from_thread(self.loading_timer.stop)

        self.app.call_from_thread(
            self.app.query_one(Label).update, f"Playing {song_title}"
        )


# === Main App ===
class EstiaApp(App):
    TITLE = "Estia"

    CSS_PATH = "estai.tcss"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()

    def compose(self) -> ComposeResult:
        self.music = EstiaPlayer()

        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        yield Pomodoro()

        search_widget = MusicSearch()
        search_widget.player = self.music

        yield search_widget
        yield Label("Nothing has been selected yet")
        yield Footer()


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
