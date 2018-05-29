import re
from abc import ABCMeta, abstractmethod

import six
from cached_property import cached_property

from icq.constant import ImageType, VideoType, AudioType
from icq.util import decode_file_id


class Filter(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(Filter, self).__init__()

    def __call__(self, event):
        return self.filter(event)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return InvertFilter(self)

    @abstractmethod
    def filter(self, event):
        raise NotImplementedError


class CompositeFilter(Filter):
    def __init__(self, filter_1, filter_2):
        super(CompositeFilter, self).__init__()

        self.filter_1 = filter_1
        self.filter_2 = filter_2

    @abstractmethod
    def filter(self, event):
        raise NotImplementedError


class AndFilter(CompositeFilter):
    def __init__(self, filter_1, filter_2):
        super(AndFilter, self).__init__(filter_1, filter_2)

    def filter(self, event):
        return self.filter_1(event) and self.filter_2(event)


class OrFilter(CompositeFilter):
    def __init__(self, filter_1, filter_2):
        super(OrFilter, self).__init__(filter_1, filter_2)

    def filter(self, event):
        return self.filter_1(event) or self.filter_2(event)


class AllFilter(Filter):
    def __init__(self, iterable):
        super(AllFilter, self).__init__()

        self.iterable = iterable

    def filter(self, event):
        return all(f(event) for f in self.iterable)


class AnyFilter(Filter):
    def __init__(self, iterable):
        super(AnyFilter, self).__init__()

        self.iterable = iterable

    def filter(self, event):
        return any(f(event) for f in self.iterable)


class InvertFilter(Filter):
    def __init__(self, filter_):
        super(InvertFilter, self).__init__()

        self.filter_ = filter_

    def filter(self, event):
        return not self.filter_(event)


class MessageFilter(object):
    class _AllFilter(Filter):
        def filter(self, event):
            return True

    all = _AllFilter()

    class _MessageFilter(Filter):
        def filter(self, event):
            return "message" in event.data and isinstance(event.data["message"], six.string_types)

    message = _MessageFilter()

    class _CommandFilter(Filter):
        COMMAND_PREFIXES = ("/", ".")

        def filter(self, event):
            return (
                MessageFilter.message(event) and
                any(event.data["message"].strip().startswith(p) for p in MessageFilter._CommandFilter.COMMAND_PREFIXES)
            )

    command = _CommandFilter()

    class _StickerFilter(Filter):
        STICKER_ID_REGEXP = re.compile(r"^ext:(?P<ext>\d+):sticker:(?P<sticker>\d+)$")

        def filter(self, event):
            return "stickerId" in event.data

    sticker = _StickerFilter()

    class _FileFilter(Filter):
        FILE_URL_REGEXP = re.compile(
            r"^[hH][tT][tT][pP][sS]?://(?:[fF][iI][lL][eE][sS]\.[iI][cC][qQ]\.[nN][eE][tT]/get|(?:[wW][wW][wW]\.)?[iI]["
            r"cC][qQ]\.[cC][oO][mM]/files|[cC][hH][aA][tT]\.[mM][yY]\.[cC][oO][mM]/files)/(?P<file_id>[a-zA-Z0-9]{32,})"
            r"(?:\?.*)?$"
        )

        def filter(self, event):
            return (
                MessageFilter.message(event) and
                MessageFilter._FileFilter.FILE_URL_REGEXP.search(event.data["message"].strip())
            )

    file = _FileFilter()

    class _ImageFilter(Filter):
        def filter(self, event):
            match = MessageFilter.file(event)
            return match and type(decode_file_id(match.group("file_id")).file_type) is ImageType

    image = _ImageFilter()

    class _VideoFilter(Filter):
        def filter(self, event):
            match = MessageFilter.file(event)
            return match and type(decode_file_id(match.group("file_id")).file_type) is VideoType

    video = _VideoFilter()

    class _AudioFilter(Filter):
        def filter(self, event):
            match = MessageFilter.file(event)
            return match and type(decode_file_id(match.group("file_id")).file_type) is AudioType

    audio = _AudioFilter()

    class _URLFilter(Filter):
        URL_REGEXP = re.compile(r"^https?://\S+$", re.IGNORECASE)

        @cached_property
        def _filter(self):
            return AndFilter(MessageFilter.message, InvertFilter(MessageFilter.file))

        def filter(self, event):
            return (
                self._filter(event) and
                MessageFilter._URLFilter.URL_REGEXP.search(event.data["message"].strip()) is not None
            )

    url = _URLFilter()

    class _TextFilter(Filter):
        @cached_property
        def _filter(self):
            return AndFilter(MessageFilter.message, InvertFilter(AnyFilter(
                (MessageFilter.command, MessageFilter.sticker, MessageFilter.file, MessageFilter.url)
            )))

        def filter(self, event):
            return self._filter(event)

    text = _TextFilter()

    class _ChatFilter(Filter):
        def filter(self, event):
            return "MChat_Attrs" in event.data

    chat = _ChatFilter()
