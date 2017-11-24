from abc import ABCMeta, abstractmethod

from icq.event import EventType
from icq.filter import MessageFilter


class Handler(object):
    __metaclass__ = ABCMeta

    def __init__(self, callback):
        super(Handler, self).__init__()

        self.callback = callback

    @abstractmethod
    def check(self, event):
        raise NotImplementedError

    def handle(self, event, dispatcher):
        return self.callback(bot=dispatcher.bot, event=event)


class MessageHandler(Handler):
    def __init__(self, callback, filters=None):
        super(MessageHandler, self).__init__(callback=callback)

        self.filters = filters

    def check(self, event):
        return event.type_ is EventType.IM and (self.filters is None or self.filters(event))


class UserAddedToBuddyListHandler(Handler):
    def check(self, event):
        return event.type_ is EventType.USER_ADDED_TO_BUDDY_LIST


class CommandHandler(MessageHandler):
    def __init__(self, callback, command=None):
        super(CommandHandler, self).__init__(callback=callback, filters=MessageFilter.command)

        self.command = command

    def check(self, event):
        return super(CommandHandler, self).check(event) and (not self.command or any(
            event.data["message"][1:].strip().lower() == c.lower() for c in (
                (self.command,) if isinstance(self.command, str) else self.command
            )
        ))


class FeedbackCommandHandler(CommandHandler):
    def message_callback(self, bot, event):
        bot.send_im(target=self.target, message=event.data["message"])

    def __init__(self, command, target):
        super(FeedbackCommandHandler, self).__init__(callback=self.message_callback, command=command)

        self.target = target


class UnknownCommandHandler(MessageHandler):
    def __init__(self, callback):
        super(UnknownCommandHandler, self).__init__(callback=callback, filters=MessageFilter.command)

    def handle(self, event, dispatcher):
        if not any(h.check(event) for h in dispatcher.handlers if isinstance(h, CommandHandler)):
            return super(UnknownCommandHandler, self).handle(event=event, dispatcher=dispatcher)


class TypingHandler(Handler):
    def check(self, event):
        return event.type_ is EventType.TYPING
