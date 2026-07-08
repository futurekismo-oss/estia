from textual.app import ComposeResult
from textual.widgets import Button, Digits
from textual.reactive import reactive
from textual.containers import Horizontal, Vertical


class Pomodoro(Vertical):
    set_time_to_minutes = 0.1  # minutes
    time = reactive(set_time_to_minutes * 60)  # 20 Seconds for now

    def on_mount(self) -> None:
        self.digits = self.query_one("#time", Digits)
        self.update_timer = self.set_interval(1 / 60, self.update_time, pause=True)

    def update_time(self):
        self.time -= 1 / 60
        if self.time <= 0:
            self.time = self.set_time_to_minutes * 60
            self.remove_class("started")
            self.update_timer.pause()

    def watch_time(self):
        minutes, seconds = divmod(self.time, 60)
        text = f"{minutes:02.0f}:{seconds:02.0f}"
        if hasattr(self, "digits"):
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
