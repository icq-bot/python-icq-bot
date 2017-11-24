from collections import namedtuple

from baseconv import BaseConverter

from icq.constant import ImageType, VideoType, AudioType

BASE62_ICQ_CONVERTER = BaseConverter("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")


def decode_file_id(file_id):
    type_ = file_id[0]
    for t in (ImageType, VideoType, AudioType):
        try:
            type_ = t(type_)
            break
        except ValueError:
            pass
    else:
        raise ValueError("Unknown file type '{}'!".format(type_))

    cls = type(type_)
    width = height = length = None
    if cls in (ImageType, VideoType):
        width = int(BASE62_ICQ_CONVERTER.decode(file_id[1:3]))
        height = int(BASE62_ICQ_CONVERTER.decode(file_id[3:5]))
    elif cls is AudioType:
        length = int(BASE62_ICQ_CONVERTER.decode(file_id[3:5]))

    return namedtuple("DecodedFileID", ("type", "width", "height", "length"))(type_, width, height, length)
