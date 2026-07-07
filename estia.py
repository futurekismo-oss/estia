import db
from player import EstiaPlayer
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Welcome


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


class EstiaApp(App):
    TITLE = "Estia"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()
        self.music = EstiaPlayer()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        yield Footer()

    def on_button_pressed(self) -> None:
        self.exit()


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
