from textual.app import ComposeResult
from textual.widgets import Button, Digits, Select, Label
from textual.reactive import reactive
from textual.containers import Vertical
from textual import on
import time
from Widgets.MusicSearch import MusicSearch
from player import EstiaPlayer


def min_to_sec(no: int) -> int:
    return no * 60  # <- Remeber to add * 60 back


class Pomodoro(Vertical):
    POMODORO_ROUTINES = {
        5: [("Work", 1), ("Break", 1)],
        45: [("Work", 15), ("Break", 10), ("Work", 15)],
        60: [("Work", 25), ("Break", 5), ("Work", 25), ("Break", 5)],
        120: [
            ("Work", 25),
            ("Break", 5),
            ("Work", 25),
            ("Break", 5),
            ("Work", 25),
            ("Break", 5),
            ("Work", 25),
            ("Break", 5),
        ],
    }

    pomodoro_times = [("5 min", 5), ("45 min", 45), ("1 hr", 60), ("2 hrs", 120)]

    time_left: int = reactive(min_to_sec(45))  # ty: ignore

    def __init__(self) -> None:
        super().__init__()
        self.current_routine = []
        self.current_stage_idx = 0

    def on_mount(self) -> None:
        self.digits = self.query_one("#time", Digits)
        self.end_time = 0.0
        self.total_paused_time = 0.0
        self.pause_start = 0.0
        self.update_timer = self.set_interval(0.1, self.update_time, pause=True)
        self.current_stage_indicator = self.query_one("#current_stage_indicator", Label)
        self.player: EstiaPlayer = self.app.query_one(MusicSearch).player

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
            if self.current_stage_index + 1 < len(self.current_routine):
                self.current_stage_index += 1
                stage_name, stage_minutes = self.current_routine[
                    self.current_stage_index
                ]

                if not self.current_stage_index % 2:  # Is even
                    self.player.player.volume = 0
                    self.app.notify("Break, reducing volume")
                else:
                    self.player.player.volume = 100

                self.current_stage_indicator.update(stage_name)

                seconds_for_stage = min_to_sec(stage_minutes)
                self.end_time = time.monotonic() + seconds_for_stage

                self.time_left = seconds_for_stage

                self.app.notify(f"Switching to {stage_name}")
            else:
                selector = self.query_one("#Select", Select)

                self.when_select_changed(selector)

                self.end_time = 0.0
                self.pause_start = 0.0
                self.remove_class("started")
                self.update_timer.pause()
        else:
            self.time_left = remaining  # ty: ignore

    def watch_time_left(self, time_left: float) -> None:
        minutes, seconds = divmod(max(0.0, time_left), 60)
        hours, minutes = divmod(minutes, 60)
        text = f"{hours:02,.0f}:{minutes:02.0f}:{seconds:02.0f}"
        if hasattr(self, "digits"):
            self.digits.update(text)

    def compose(self) -> ComposeResult:
        yield Label("Test", id="current_stage_indicator")
        yield Digits("25:00", id="time")
        yield Button("", variant="success", id="start", classes="timer_btn")
        yield Button("", id="stop", variant="error", classes="timer_btn")
        yield Select(
            self.pomodoro_times,
            id="Select",
            allow_blank=False,
        )

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id == "start":
            self.add_class("started")
            self.start_timer()
        elif button_id == "stop":
            self.remove_class("started")
            self.pause_timer()

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.when_select_changed(event)

    def when_select_changed(self, event) -> None:
        total_minutes = event.value

        self.current_routine = self.POMODORO_ROUTINES.get(
            total_minutes, [("Work", total_minutes)]
        )
        self.current_stage_index = 0

        first_stage_name, first_stage_minutes = self.current_routine[0]
        self.time_left = min_to_sec(first_stage_minutes)
        self.current_stage_indicator.update(first_stage_name)
