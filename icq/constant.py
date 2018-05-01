from enum import Enum, unique


@unique
class TypingStatus(Enum):
    LOOKING = "looking"  # Looking into active dialog.
    TYPING = "typing"  # Started typing, only send on transition, but not for every key press.
    TYPED = "typed"  # Previously was typing and now has stopped typing.
    NONE = "none"  # Previously was in typing or typed status and has erased all their text.


@unique
class ChatDefaultRole(Enum):
    MEMBER = "member"
    READONLY = "readonly"


@unique
class UserChatRole(Enum):
    ADMIN = "admin"
    MODER = "moder"
    MEMBER = "member"


@unique
class ImageType(Enum):
    REGULAR = "0"
    SNAP = "1"
    STICKER = "2"
    RESERVED_3 = "3"
    IMAGE_ANIMATED = "4"
    STICKER_ANIMATED = "5"
    RESERVED_6 = "6"
    RESERVED_7 = "7"


@unique
class VideoType(Enum):
    REGULAR = "8"
    SNAP = "9"
    PTS = "A"
    PTS_B = "B"
    RESERVED_C = "C"
    STICKER = "D"
    RESERVED_E = "E"
    RESERVED_F = "F"


@unique
class AudioType(Enum):
    REGULAR = "G"
    SNAP = "H"
    PTT = "I"
    PTT_J = "J"
    RESERVED_K = "K"
    RESERVED_L = "L"
    RESERVED_M = "M"
    RESERVED_N = "N"


@unique
class MessageParseType(Enum):
    URL = "url"
    FILE_SHARING = "filesharing"


@unique
class StickerSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
