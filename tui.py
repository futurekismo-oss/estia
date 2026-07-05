from blessed import Terminal
import time
import builtins as __builtin__

term = Terminal()
print(term.clear)


def print(*args, **kwargs):
    return __builtin__.print(*args, **kwargs, end="", flush=True)


bar_len = 10
total_steps = 100

def progress_bar(value, bar_len=10):
    # ratio = current_step / total_steps
    ratio = value / 100

    num_filled = int(ratio * bar_len)

    num_empty = bar_len - num_filled

    bar_string = "█" * num_filled + "-" * num_empty


    return f"[{bar_string}] {value:3d}%"

setattr(term, 'progress_bar', progress_bar)



print("\n")
