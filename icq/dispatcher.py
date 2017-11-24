import logging

from icq.handler import Handler


class Dispatcher(object):
    def __init__(self, bot):
        super(Dispatcher, self).__init__()

        self.log = logging.getLogger(__name__)

        self.bot = bot
        self.handlers = []

    def add_handler(self, handler):
        if not isinstance(handler, Handler):
            raise TypeError("Parameter 'handler' must be an instance of {} class!".format(Handler.__name__))

        self.handlers.append(handler)

    def remove_handler(self, handler):
        if not isinstance(handler, Handler):
            raise TypeError("Parameter 'handler' must be an instance of {} class!".format(Handler.__name__))

        if handler in self.handlers:
            self.handlers.remove(handler)

    def dispatch(self, event):
        try:
            for handler in (h for h in self.handlers if h.check(event)):
                handler.handle(event, self)
        except Exception:
            self.log.exception("Exception while handling event!")
            raise
