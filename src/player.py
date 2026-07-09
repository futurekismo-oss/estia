import mpv
from ytmusicapi import YTMusic
from textual.widgets import Label


class EstiaPlayer:
    def __init__(self, app_instance):
        self.app = (
            app_instance  # Ensure your player class has a reference to the Textual app
        )
        self.player = mpv.MPV(video=False, ytdl=True)
        self.ytmusic = YTMusic()

        @self.player.event_callback("end-file")
        def on_file_end(event):
            event_data = event.as_dict()

            if "reason" in event_data:
                reason_code = event_data["reason"]

                if reason_code == b"eof" or reason_code == 0:
                    self.app.call_from_thread(
                        self.app.query_one("#label", Label).update,
                        "Song finished! Ready for the next one.",
                    )
                    self.app.call_from_thread(
                        self.app.notify("Song finished! Ready for the next one")
                    )

    def search_songs(self, query: str, limit: int = 10):
        return self.ytmusic.search(
            query,
            filter="songs",
        )[:limit]

    def play_song(self, video_id: str):
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        self.player.play(youtube_link)

    def stop(self):
        self.player.terminate()
