from textual.reactive import reactive
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.widgets import Label, ListView, ListItem


class Playlist(Vertical):
    playlist_list: ListView
    playlist_label: Label
    playlist: list[tuple] = reactive([])  # ty: ignore

    def compose(self) -> ComposeResult:
        yield ListView(id="playlist_list")
        yield Label("Working", id="playlist_label")

    def on_mount(self) -> None:
        self.playlist_list = self.query_one("#playlist_list", ListView)
        self.playlist_label = self.query_one("#playlist_label", Label)

    def watch_playlist(self) -> None:
        if len(self.playlist) == 0:
            return

        self.playlist_list.clear()

        for tracks in self.playlist:
            self.playlist_list.append(ListItem(Label(str(tracks[0]))))

    def add_track_safely(self, title: str, track_id: str) -> None:
        self.playlist.append((title, track_id))

        self.call_next(self._append_widget, title)

    def _append_widget(self, title: str) -> None:
        self.playlist_list.append(ListItem(Label(str(title))))
