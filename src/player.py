import mpv
from ytmusicapi import YTMusic


class EstiaPlayer:
    def __init__(self):
        self.player = mpv.MPV(video=False, ytdl=True)
        self.ytmusic = YTMusic()

        @self.player.event_callback("end-file")
        def on_file_end(event):
            event_data = event.as_dict()

            if "reason" in event_data:
                reason_code = event_data["reason"]

                if reason_code == b"eof" or reason_code == 0:
                    print(
                        "The song finished playing naturally! Put your next song logic here."
                    )
                elif reason_code == b"stop" or reason_code == 3:
                    print("Playback was manually stopped.")

    def search_songs(self, query: str, limit: int = 5):
        return self.ytmusic.search(query, filter="songs")[:limit]

    def play_song(self, video_id: str):
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        self.player.play(youtube_link)

    def stop(self):
        self.player.terminate()
