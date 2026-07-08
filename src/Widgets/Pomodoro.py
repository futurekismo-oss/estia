from textual.app import ComposeResult
from textual.widgets import Button, Digits
from textual.reactive import reactive
from textual.containers import Vertical
import time


class Pomodoro(Vertical):
    set_time_to_minutes = 25  # minutes
    time_left: reactive[float] = reactive(
        set_time_to_minutes * 60
    )  # 20 Seconds for now

    def on_mount(self) -> None:
        self.digits = self.query_one("#time", Digits)
        self.end_time = 0.0
        self.total_paused_time = 0.0
        self.pause_start = 0.0
        self.update_timer = self.set_interval(0.1, self.update_time, pause=True)

    def start_timer(self) -> None:
        if self.end_time == 0.0:
            self.end_time = time.monotonic() + self.time_left
        elif self.pause_start > 0.0:
            self.end_time += time.monotonic() - self.pause_start
            self.pause_start = 0.0

        self.add_class("started")
        self.update_timer.resume()

    def pause_timer(self) -> None:
        if self.pause_start == 0.0 and self.end_time > 0.0:
            self.pause_start = time.monotonic()
            self.update_timer.pause()
            self.remove_class("started")

    def update_time(self) -> None:
        remaining = self.end_time - time.monotonic()

        if remaining <= 0:
            self.time_left = self.set_time_to_minutes * 60
            self.end_time = 0.0
            self.pause_start = 0.0
            self.remove_class("started")
            self.update_timer.pause()
        else:
            self.time_left = remaining

    def watch_time_left(self, time_left: float) -> None:
        minutes, seconds = divmod(max(0.0, time_left), 60)
        text = f"{minutes:02.0f}:{seconds:02.0f}"
        if hasattr(self, "digits"):
            self.digits.update(text)

    def compose(self) -> ComposeResult:
        yield Digits("25:00", id="time")
        yield Button("", variant="success", id="start")
        yield Button("", id="stop", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "start":
            self.add_class("started")
            self.start_timer()
        elif button_id == "stop":
            self.remove_class("started")
            self.pause_timer()
