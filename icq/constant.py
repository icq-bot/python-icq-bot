from enum import Enum


class TypingStatus(Enum):
    LOOKING = "looking"  # Looking into active dialog.
    TYPING = "typing"  # Started typing, only send on transition, but not for every key press.
    TYPED = "typed"  # Previously was typing and now has stopped typing.
    NONE = "none"  # Previously was in typing or typed status and has erased all their text.


class ImageType(Enum):
    REGULAR = "0"
    SNAP = "1"
    STICKER = "2"
    RESERVED_3 = "3"
    IMAGE_ANIMATED = "4"
    STICKER_ANIMATED = "5"
    RESERVED_6 = "6"
    RESERVED_7 = "7"


class VideoType(Enum):
    REGULAR = "8"
    SNAP = "9"
    PTS = "A"
    PTS_RESERVED = "B"
    RESERVED_C = "C"
    STICKER = "D"
    RESERVED_E = "E"
    RESERVED_F = "F"


class AudioType(Enum):
    REGULAR = "G"
    SNAP = "H"
    PTT_I = "I"
    PTT_RESERVED = "J"
    RESERVED_K = "K"
    RESERVED_L = "L"
    RESERVED_M = "M"
    RESERVED_N = "N"
