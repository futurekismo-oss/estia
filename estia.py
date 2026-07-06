import db
import tui
import stages
from player import EstiaPlayer


def run_app():
    db.init_database()
    music = EstiaPlayer()
    term = tui.term

    print(term.set_window_title("Estia"))

    try:
        with term.cbreak(), term.hidden_cursor(), term.fullscreen():
            stages.intro(music)
            stages.music_search_input()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        music.stop()
        print(term.normal + "\nSession closed. Goodbye!\n")


if __name__ == "__main__":
    run_app()
