from abc import ABCMeta, abstractmethod

from icq.dispatcher import StopDispatch
from icq.event import EventType
from icq.filter import MessageFilter


class Handler(object):
    __metaclass__ = ABCMeta

    def __init__(self, callback):
        super(Handler, self).__init__()

        self.callback = callback

    @abstractmethod
    def check(self, event, dispatcher):
        raise NotImplementedError

    def handle(self, event, dispatcher):
        self.callback(bot=dispatcher.bot, event=event)


class DefaultHandler(Handler):
    def __init__(self, callback):
        super(DefaultHandler, self).__init__(callback)

    def check(self, event, dispatcher):
        return not any(h.check(event=event, dispatcher=dispatcher) for h in dispatcher.handlers if h is not self)

    def handle(self, event, dispatcher):
        super(DefaultHandler, self).handle(event, dispatcher)
        raise StopDispatch


class MessageHandler(Handler):
    def __init__(self, callback, filters=None):
        super(MessageHandler, self).__init__(callback=callback)

        self.filters = filters

    def check(self, event, dispatcher):
        return event.event_type is EventType.IM and bool(not self.filters or self.filters(event))


class UserAddedToBuddyListHandler(Handler):
    def check(self, event, dispatcher):
        return event.event_type is EventType.USER_ADDED_TO_BUDDY_LIST


class CommandHandler(MessageHandler):
    def __init__(self, callback, command=None):
        super(CommandHandler, self).__init__(callback=callback, filters=MessageFilter.command)

        self.command = command

    def check(self, event, dispatcher):
        return super(CommandHandler, self).check(event=event, dispatcher=dispatcher) and (not self.command or any(
            event.data["message"].partition(" ")[0][1:].strip().lower() == c.lower() for c in (
                (self.command,) if isinstance(self.command, str) else self.command
            )
        ))


class FeedbackCommandHandler(CommandHandler):
    def message_callback(self, bot, event):
        bot.send_im(target=self.target, message="Feedback from '{source_uin}': '{message}'.".format(
            source_uin=event.data["source"]["aimId"], message=event.data["message"].partition(" ")[2]
        ))

    def __init__(self, target, command="feedback"):
        super(FeedbackCommandHandler, self).__init__(callback=self.message_callback, command=command)

        self.target = target


class UnknownCommandHandler(MessageHandler):
    def __init__(self, callback):
        super(UnknownCommandHandler, self).__init__(callback=callback, filters=MessageFilter.command)

    def check(self, event, dispatcher):
        return super(UnknownCommandHandler, self).check(event=event, dispatcher=dispatcher) and not any(
            h.check(event=event, dispatcher=self) for h in dispatcher.handlers if isinstance(h, CommandHandler)
        )

    def handle(self, event, dispatcher):
        super(UnknownCommandHandler, self).handle(event, dispatcher)
        raise StopDispatch


class TypingHandler(Handler):
    def check(self, event, dispatcher):
        return event.event_type is EventType.TYPING


class SentIMHandler(Handler):
    def check(self, event, dispatcher):
        return event.event_type is EventType.SENT_IM
