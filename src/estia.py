import db
from player import EstiaPlayer

from textual import work
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, OptionList, Label, ListView
from textual.geometry import Offset


from textual_drivers._dnd_app import Drop, DropData
from textual_drivers.dnd import (
    DNDApp,
    DNDDragOutOperation,
    DragOutFinished,
    DNDDragIn,
    DNDDragInOperation,
)


# === Widgets ===
from Widgets.Pomodoro import Pomodoro
from Widgets.MusicSearch import MusicSearch
from Widgets.Playlist import Playlist


# === Utils Funcs ===
def set_window_title(title: str) -> None:
    print(f"\033]2;{title}\007", end="", flush=True)


# === Main App ===
class EstiaApp(DNDApp, App):
    TITLE = "Estia"

    CSS_PATH = "estai.tcss"

    SUBTITLE = "Pomodoro & Music Player"

    def on_mount(self) -> None:
        db.init_database()
        self.zone = self.app.query_one("#playlist_list", ListView)
        self.playlist_instance = self.app.query_one(Playlist)

    def compose(self) -> ComposeResult:
        self.music = EstiaPlayer(self)

        yield Header(show_clock=True, icon="󰔟", time_format="%I:%M %p", name="Estia")

        yield Pomodoro()

        search_widget = MusicSearch()
        search_widget.player = self.music

        yield search_widget

        yield Playlist()
        yield Footer()

    async def dnd_drag_out_operation(self, pos: Offset) -> DNDDragOutOperation | None:
        results_list = self.app.query_one(OptionList)

        if not results_list.region.contains(*pos):
            return

        mouse_hovering = results_list._mouse_hovering_over

        if not mouse_hovering:
            return None

        selected = results_list.get_option_at_index(mouse_hovering)

        if not selected:
            return None

        name = [selected.id]

        text = str(selected.prompt)

        return DNDDragOutOperation(name, "copy", text, 1)  # ty: ignore

    async def on_drag_out_finished(self, event: DragOutFinished) -> None:
        pass

    @work
    async def on_drop(self, event: Drop) -> None:
        self.request_data(event, 0, close=True)

    def on_drop_data(self, event: DropData) -> None:
        results_list = self.app.query_one(OptionList)
        if not results_list:
            return

        answer = None
        if isinstance(event.data, list) and event.data:
            dropped_id = event.data[0]
        else:
            dropped_id = event.data

        for index in range(results_list.option_count):
            option = results_list.get_option_at_index(index)
            if option.id == dropped_id:
                answer = option
                break

        if answer:
            self.playlist_instance.add_track_safely(answer.prompt, answer.id)  # ty:ignore
        else:
            self.app.notify("Dropped item not found")

    async def on_dnddrag_in(self, event: DNDDragIn) -> None:
        label = self.app.query_one("#playlist_label", Label)

        if self.zone.region.contains(*event.pos):
            label.update("In region")
        else:
            label.update("Out of region")

    async def dnd_drag_in_operation(
        self, event: DNDDragIn
    ) -> DNDDragInOperation | bool:
        is_accepted = self.zone.region.contains(*event.pos)

        return DNDDragInOperation(
            accepted=is_accepted,
            op="either",
            mimes=event.mimes,
        )


if __name__ == "__main__":
    set_window_title("Estia")
    app = EstiaApp()
    app.run()
