from tui import (
    get_len,
    get_text_center_x,
    print_with_bars,
    term,
    typing_effect,
    center_y,
    printt,
)
from player import EstiaPlayer


def intro(music: EstiaPlayer):
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

        # \x11 is Ctrl+Q, \x03 is Ctrl+C
        if kp == "\x03":
            raise SystemExit

        if kp.name == "KEY_ENTER" and user_search:
            break
        elif kp.name == "KEY_BACKSPACE":
            user_search = user_search[:-1]
        elif not kp.is_sequence:
            user_search += kp
        printt(
            term.move_xy(get_text_center_x(prompt + user_search), center_y)
            + term.clear_eol
            + prompt
            + user_search
        )
