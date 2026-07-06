from blessed import Terminal
import builtins as __builtin__
import time


term = Terminal()


center_x: int = term.width // 2
center_y: int = term.height // 2


def printt(*args, **kwargs):
    return __builtin__.print(*args, **kwargs, end="", flush=True)


def progress_bar(value: float, bar_len=20):
    # ratio = current_step / total_steps
    ratio = value / 100

    num_filled = int(ratio * bar_len)

    num_empty = bar_len - num_filled

    bar_string = "█" * num_filled + "-" * num_empty

    return f"[{bar_string}] {value:3d}%"


def typing_effect(text: str, x: int, y: int, delay=0.1):

    printt(term.move_xy(x, y))

    for part in term.split_seqs(text):
        printt(part)

        if part.startswith("\x1b"):
            time.sleep(0.1)
            continue

        key = term.inkey(timeout=delay)
        if key:
            return key
    return None


def print_with_bars(text: str, x: int, y: int):

    printt(term.move_xy(x - 1, y) + "[")
    printt(term.move_xy(x + get_len(text), y) + "]")

    printt(term.move_xy(x, y))

    printt(text)


def get_text_center_x(text):
    return (term.width - len(term.strip_seqs(text))) // 2


def get_len(text):
    return len(term.strip_seqs(text))


def __unused():
    printt(
        term.move_xy(0, center_y) + term.clear_eol
    )  # Clear the row when the intro finishes

    while True:
        quit_text = "Press [q] to quit"
        print_with_bars(quit_text, term.width - get_len(quit_text) - 2, term.height - 2)
        key = term.inkey(0.5)

        if key.lower() == "q":
            break

    printt("\nQuit Bye\n")
