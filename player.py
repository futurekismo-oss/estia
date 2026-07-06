import mpv
from ytmusicapi import YTMusic


class EstiaPlayer:
    def __init__(self):
        self.player = mpv.MPV(video=False, ytdl=True)
        self.ytmusic = YTMusic()

    def search_songs(self, query: str, limit: int = 5):
        return self.ytmusic.search(query, filter="songs")[:limit]

    def play_song(self, video_id: str):
        youtube_link = f"https://www.youtube.com/watch?v={video_id}"
        self.player.play(youtube_link)
        self.player.wait_until_playing()

    def stop(self):
        self.player.terminate()
