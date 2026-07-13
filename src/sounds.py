import os
from pygame import mixer


class Sfx:
    def __init__(self):
        mixer.init()

    def load_sound(self, file_path: str) -> mixer.Sound:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file {file_path} not found ")

        return mixer.Sound(file_path)

    def play_sound(self, sound):
        if sound:
            sound.play()
