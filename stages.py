from tui import (
    get_len,
    get_text_center_x,
    print_with_bars,
    term,
    typing_effect,
    center_y,
    printt,
    progress_bar,
)
from player import EstiaPlayer
from pyfzf.pyfzf import FzfPrompt


def intro():
    skip_key = "x"
    with term.cbreak(), term.hidden_cursor(), term.fullscreen():
        skip_text = f"Press [{skip_key}] to skip"
        bottom_left_x, bottom_left_y = (
            term.width - get_len(skip_text) - 2,
            term.height - 2,
        )

        print_with_bars(skip_text, bottom_left_x, bottom_left_y)

        intro = [
            "Hello, Nice to meet you",
            f"This is {term.magenta_bold('Estia')}",
            "A Pomodromo Timer with lofi music built-in",
            "It also logs your sessions and renders them as beautfiul charts",
            f"Made by {term.link('https://github.com/futurekismo-oss', term.magenta_bold_italic('Futurekismo'))}",
        ]

        for text in intro:
            text_length = get_len(text)
            start_x = get_text_center_x(text)

            printt(term.move_xy(0, center_y) + term.clear_eol)

            printt(term.move_xy(start_x - 1, center_y) + "[")
            printt(term.move_xy(start_x + text_length, center_y) + "]")

            key_pressed = typing_effect(text, start_x, center_y, delay=0.05)

            printt(term.normal)
            if not key_pressed:
                key_pressed = term.inkey(timeout=1.0)

            if key_pressed:
                # \x11 is Ctrl+Q, \x03 is Ctrl+C
                if key_pressed == "\x03":
                    raise SystemExit
                elif key_pressed.lower() == skip_key:
                    break


def music_search_input():
    printt(term.clear)
    prompt = "Search for lofi/music: "
    printt(term.move_xy(get_text_center_x(prompt), center_y) + prompt)

    user_search = ""
    while True:
        kp = term.inkey()

        if kp == "\x03":
            raise SystemExit

        if kp.name == "KEY_ENTER" and user_search:
            break
        elif kp.name == "KEY_BACKSPACE":
            user_search = user_search[: len(user_search) - 1]
        elif not kp.is_sequence:
            user_search += kp
        printt(
            term.move_xy(get_text_center_x(user_search), center_y + 1)
            + term.clear_eol
            + term.clear_bol
            + user_search
        )

    return user_search


def display_and_choose_songs(user_search, music: EstiaPlayer):
    results = music.search_songs(user_search, limit=20)
    if not results:
        return None

    song_map = {song["title"]: song for song in results}
    choices = list(song_map.keys())

    fzf = FzfPrompt()

    printt(term.clear)

    try:
        selected_titles = fzf.prompt(
            choices,
            '--header="Use arrows to pick a song, Esc to exit" --reverse --height=40%',
        )

        if selected_titles:
            chosen_title = selected_titles[0]
            return song_map[chosen_title]
    except Exception:
        pass

    return None


def play_and_animate_song(song, music):
    if not song:
        return

    music.play_song(song["videoId"])
    printt(term.clear)

    # Vinyl disc frame variations for the rotating text effect
    disc_frames = [
        " ┌───┐ \n │ / │ \n └───┘ ",
        " ┌───┐ \n │ | │ \n └───┘ ",
        " ┌───┐ \n │ \\ │ \n └───┘ ",
        " ┌───┐ \n │ — │ \n └───┘ ",
    ]

    frame_idx = 0

    try:
        while True:
            key = term.inkey(timeout=0.1)

            if key == "\x03" or key.lower() == "q":
                music.stop()
                break

            elif key == " ":  # Space key
                music.player.pause = not music.player.pause
                printt(term.clear)

            time_pos = music.player.time_pos or 0.0
            duration = music.player.duration or 1.0
            is_paused = music.player.pause

            title_line = f"Now Playing: {term.magenta_bold(song['title'])}"

            current_stamp = f"{int(time_pos) // 60}:{int(time_pos) % 60:02d}"
            total_stamp = f"{int(duration) // 60}:{int(duration) % 60:02d}"

            percent_complete = min(100, int((time_pos / duration) * 100))
            prog_string = progress_bar(percent_complete, bar_len=25)
            status_line = f"{current_stamp} {prog_string} {total_stamp}"

            controls_line = "[SPACE] Pause/Play  |  [Q] to quit"
            if is_paused:
                controls_line = (
                    f"|| {term.yellow('PAUSED')} ||  [SPACE] Resume  |  [Q] Quit"
                )

            if not is_paused:
                frame_idx = (frame_idx + 1) % len(disc_frames)

                from time import sleep

                sleep(0.1)

            lines_of_disc = disc_frames[frame_idx].split("\n")
            for offset, disc_row in enumerate(lines_of_disc):
                printt(
                    term.move_xy(get_text_center_x(disc_row), (center_y - 5) + offset)
                    + term.clear_eol
                    + disc_row
                )

            printt(
                term.move_xy(get_text_center_x(title_line), center_y - 1)
                + term.clear_eol
                + title_line
            )

            printt(
                term.move_xy(get_text_center_x(status_line), center_y + 1)
                + term.clear_eol
                + status_line
            )

            printt(
                term.move_xy(get_text_center_x(controls_line), center_y + 4)
                + term.clear_eol
                + term.dim
                + controls_line
            )

    except Exception:
        music.stop()
        raise SystemExit

    printt(term.clear)
