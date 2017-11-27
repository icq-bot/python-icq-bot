import logging


class Dispatcher(object):
    def __init__(self, bot):
        super(Dispatcher, self).__init__()

        self.log = logging.getLogger(__name__)

        self.bot = bot
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)

    def dispatch(self, event):
        try:
            for handler in (h for h in self.handlers if h.check(event=event, dispatcher=self)):
                handler.handle(event=event, dispatcher=self)
        except StopDispatch:
            self.log.debug("StopDispatch caught, stopping dispatching.")
        except Exception:
            self.log.exception("Exception while handling event!")
            raise


class StopDispatch(Exception):
    """ If raised from handler 'check' or 'handle' methods then dispatching will be stopped. """
    pass
