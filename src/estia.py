import db
from player import EstiaPlayer

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer

# === Widgets ===
from Widgets.Pomodoro import Pomodoro
from Widgets.MusicSearch import MusicSearch


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


# === Main App ===
class EstiaApp(App):
    TITLE = "Estia"

    CSS_PATH = "estai.tcss"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()

    def compose(self) -> ComposeResult:
        self.music = EstiaPlayer(self)

        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        yield Pomodoro()

        search_widget = MusicSearch()
        search_widget.player = self.music

        yield search_widget
        yield Footer()


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
