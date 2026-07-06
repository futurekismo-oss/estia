import db
import tui
import stages
from player import EstiaPlayer


def run_app():
    db.init_database()
    music = EstiaPlayer()
    term = tui.term

    print(term.set_window_title("Estia"))
    print(term.hide_cursor, end="", flush=True)

    try:
        with term.cbreak(), term.fullscreen():
            stages.intro()
            user_search = stages.music_search_input()
            song = stages.display_and_choose_songs(user_search, music)

            if song:
                stages.play_and_animate_song(song, music)

    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        music.stop()
        print(term.normal_cursor + term.normal + "\nSession closed. Goodbye!\n")


if __name__ == "__main__":
    run_app()
