import mpv
from ytmusicapi import YTMusic

player = mpv.MPV(video=False, ytdl=True)
ytmusic = YTMusic()

def get_safe_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a valid number.")

user_search = input("Search for Music: ")



search = ytmusic.search(user_search, filter='songs', limit=10)
print(f'Searching for "{user_search}" music...')

for index, music in enumerate(search):
    print(f" {index} - {music["title"]} ")


user_choice = get_safe_int("Enter a number: ")




# Get the video id of the first search
video_id = search[user_choice]["videoId"]
video_name = search[user_choice]["title"]

youtube_link = f"https://www.youtube.com/watch?v={video_id}"


player.play(youtube_link)
print(f"Fetching {youtube_link}")


player.wait_until_playing()
print(f"Playing {video_name}")


player.wait_for_playback()

# pp = pprint.PrettyPrinter(indent=4)
# pp.pprint(search[1])



