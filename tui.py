from blessed import Terminal
import time
import builtins as __builtin__

term = Terminal()
print(term.clear)

center_x: int = term.width // 2
center_y: int = term.height // 2


def print(*args, **kwargs):
    return __builtin__.print(*args, **kwargs, end="", flush=True)


def progress_bar(value: float, bar_len=20):
    # ratio = current_step / total_steps
    ratio = value / 100

    num_filled = int(ratio * bar_len)

    num_empty = bar_len - num_filled

    bar_string = "█" * num_filled + "-" * num_empty

    return f"[{bar_string}] {value:3d}%"


def typing_effect(text: str, x: int, y: int, delay=0.1):

    print(term.move_xy(x, y))

    for char in text:
        print(char)
        key = term.inkey(timeout=delay)
        if key:
            return key
    return None


def print_with_bars(text: str, x: int, y: int):

    print(term.move_xy(x - 1, y) + "[")
    print(term.move_xy(x + get_len(text), y) + "]")

    print(term.move_xy(x, y))

    print(text)


def get_text_center_x(text):
    return (term.width - len(term.strip_seqs(text))) // 2


def get_len(text):
    return len(term.strip_seqs(text))


setattr(term, "progress_bar", progress_bar)


with term.cbreak(), term.hidden_cursor(), term.fullscreen():
    intro = [
        "Hello, Nice to meet you",
        f"This is {term.magenta_bold('Estia')}",
        "A Pomodromo Timer with lofi music builtin",
    ]

    for text in intro:
        text_length = get_len(text)
        start_x = get_text_center_x(text)

        print(term.move_xy(0, center_y) + term.clear_eol)

        print(term.move_xy(start_x - 1, center_y) + "[")
        print(term.move_xy(start_x + text_length, center_y) + "]")

        key_pressed = typing_effect(text, start_x, center_y, delay=0.05)

        print(term.normal)
        if not key_pressed:
            key_pressed = term.inkey(timeout=1.0)

        if key_pressed and key_pressed.lower() == "q":
            break

    print(
        term.move_xy(0, center_y) + term.clear_eol
    )  # Clear the row when the intro finishes

    while True:
        quit_text = "Press [q] to quit"
        print_with_bars(quit_text, term.width - get_len(quit_text) - 2, term.height - 2)
        key = term.inkey(0.5)

        if key.lower() == "q":
            break


print(
    "\nQuit Bye\n"
)
