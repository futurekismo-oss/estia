import pygame
from textual.app import ComposeResult
from textual.widgets import Button, Digits, Select, Label, Static
from textual.reactive import reactive
from textual_thin_slider import ThinSlider
from textual.containers import Vertical, Horizontal
from textual import on, work
import time
from player import EstiaPlayer
from sounds import Sfx

from Widgets.Playlist import Playlist
from threading import Event


def min_to_sec(no: int) -> int:
    return no * 60  # <- Remeber to add * 60 back


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(value, max_val))


class FloatingScreen(Static):
    player: EstiaPlayer
    is_fetching: bool = False
    current_song_index: int = 0
    BINDINGS = [("space", "toggle_pause", "Play/Pause")]

    DEFAULT_CSS = """
    FloatingScreen {
        width: 25;
        height: 7;
        margin: 2 4;
        background: rgba(0, 0, 0, 0);
        border: round $accent;
        position: absolute;
    }

        """

    def on_mount(self):
        self.player = self.app.music  # ty: ignore
        self.pause_music_btn = self.query_one("#pause_music_btn", Button)
        self.result_list = self.app.query_one("#playlist", Playlist)

        self.music_title_label = self.query_one("#label", Label)
        self.progress_bar = self.query_one("#track_progress", ThinSlider)
        self.playback_time_label = self.query_one("#playback_time_label", Label)
        self.stop_playback_work = Event()
        self.is_playing = False

    def compose(self) -> ComposeResult:
        yield Label("Song Name", id="label")
        yield ThinSlider(range_min=0, range_max=100, id="track_progress")
        with Horizontal():
            yield Button(
                "▶", variant="success", classes="tiny_btn", id="play_music_btn"
            )
            yield Button(
                "⏸", variant="warning", classes="tiny_btn", id="pause_music_btn"
            )
            yield Label("[0:00 / 0:00]", id="playback_time_label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pause_music_btn":
            self.action_toggle_pause()

        if event.button.id == "play_music_btn":
            self.play_current_selection()

    def play_current_selection(self) -> None:
        MAX_TITLE_LEN = 17
        playlist = self.result_list.playlist
        if not playlist or not (0 <= self.current_song_index < len(playlist)):
            return

        song_title = playlist[self.current_song_index][0]
        video_id = playlist[self.current_song_index][1]

        if len(song_title) > MAX_TITLE_LEN:
            song_title = f"{song_title[: MAX_TITLE_LEN - 3]}..."

        self.music_title_label.update("fetching...")
        self.is_fetching = True

        self.stop_playback_work.set()
        self.stop_playback_work = Event()

        self.start_playback_worker(video_id, song_title)

    def advance_playlist(self, forward: bool = True) -> None:
        playlist = self.result_list.playlist
        if not playlist:
            return

        modifier = 1 if forward else -1
        self.current_song_index = (self.current_song_index + modifier) % len(playlist)

        self.play_current_selection()

    def action_toggle_pause(self):
        self.player.player.pause = not self.player.player.pause

    @on(ThinSlider.Changed, "#track_progress")
    def on_timeline_drag(self, event: ThinSlider.Changed) -> None:
        if event.control.has_focus:
            if self.is_playing:
                self.player.player.seek(event.value, "absolute-percent")

    @work(thread=True)  # runs on a different thread
    def start_playback_worker(self, video_id: str, song_title) -> None:
        self.player.play_song(video_id)  # so as not the block the main UI loop

        self.player.player.wait_until_playing()

        self.app.call_from_thread(self.music_title_label.update, song_title)

        self.is_playing = True
        self.is_fetching = False

        while self.player.player.duration is not None:
            if self.stop_playback_work.is_set():
                self.app.call_from_thread(setattr, self.progress_bar, "value", 0.0)
                break

            total_seconds = self.player.player.duration

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
                    self.playback_time_label.update,
                    f"[{remaining_time} / {total_time}]",
                )

            # Sleep for a second so as not max out our poor cpu
            from time import sleep

            sleep(1)

        if self.stop_playback_work.is_set():
            return

        self.app.call_from_thread(self.advance_playlist, forward=True)


class Pomodoro(Vertical):
    POMODORO_ROUTINES = {
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

    pomodoro_times = [("45 min", 45), ("1 hr", 60), ("2 hrs", 120)]

    time_left: int = reactive(min_to_sec(45))  # ty: ignore

    def __init__(self) -> None:
        super().__init__()
        self.current_routine = []
        self.current_stage_index = 0

    def on_mount(self) -> None:
        self.digits = self.query_one("#time", Digits)
        self.end_time = 0.0
        self.pause_start = 0.0
        self.update_timer = self.set_interval(0.1, self.update_time, pause=True)
        self.current_stage_indicator = self.query_one("#current_stage_indicator", Label)

        self.mixer = Sfx()
        if hasattr(pygame, "mixer") and pygame.mixer.get_init():
            self.break_sound = self.mixer.load_sound(
                self.mixer.get_sfx_asset("bell.mp3")
            )
        else:
            self.break_sound = None

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
            self.mixer.play_sound(self.break_sound)

            if self.current_stage_index + 1 < len(self.current_routine):
                self.current_stage_index += 1
                stage_name, stage_minutes = self.current_routine[
                    self.current_stage_index
                ]

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
        yield FloatingScreen()

        yield Label("Test", id="current_stage_indicator")
        yield Digits("25:00", id="time")
        yield Button("▶", variant="success", id="start", classes="timer_btn")
        yield Button("⏸", id="stop", variant="error", classes="timer_btn")
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
