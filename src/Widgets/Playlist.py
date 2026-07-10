from textual.message import Message
from textual.widgets import Label, ListView, ListItem
from textual.containers import Vertical
from textual.app import ComposeResult


class PlaylistTrackItem(ListItem):
    # A custom ListItem that knows its own track metadata.

    def __init__(self, title: str, track_id: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.title = title
        self.track_id = track_id

    def compose(self) -> ComposeResult:
        yield Label(f"󰆴 {self.title}")

    def on_click(self) -> None:
        self.post_message(self.DeleteRequested(self))

    class DeleteRequested(Message):
        def __init__(self, track_item: "PlaylistTrackItem") -> None:
            super().__init__()
            self.track_item = track_item


class Playlist(Vertical):
    playlist_list: ListView
    playlist_label: Label
    playlist: list[tuple] = []

    def compose(self) -> ComposeResult:
        yield ListView(id="playlist_list")
        yield Label("Working", id="playlist_label")

    def on_mount(self) -> None:
        self.playlist_list = self.query_one("#playlist_list", ListView)
        self.playlist_label = self.query_one("#playlist_label", Label)

    def add_track_safely(self, title: str, track_id: str) -> None:
        self.playlist.append((title, track_id))
        self.call_next(self._append_widget, title, track_id)

    def _append_widget(self, title: str, track_id: str) -> None:
        self.playlist_list.append(PlaylistTrackItem(title, track_id))

    def on_playlist_track_item_delete_requested(
        self, event: PlaylistTrackItem.DeleteRequested
    ) -> None:
        # Handles the delete request message bubbling up from the clicked track.
        track_item = event.track_item

        self.playlist = [t for t in self.playlist if t[1] != track_item.track_id]

        track_item.remove()
