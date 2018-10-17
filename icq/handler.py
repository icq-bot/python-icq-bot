from abc import ABCMeta, abstractmethod

import six

from icq.dispatcher import StopDispatch
from icq.event import EventType
from icq.filter import MessageFilter, AndFilter


class Handler(object):
    __metaclass__ = ABCMeta

    def __init__(self, callback=None):
        super(Handler, self).__init__()

        self.callback = callback

    @abstractmethod
    def check(self, event, dispatcher):
        raise NotImplementedError

    def handle(self, event, dispatcher):
        if self.callback:
            self.callback(bot=dispatcher.bot, event=event)


class DefaultHandler(Handler):
    def check(self, event, dispatcher):
        return not any(h.check(event=event, dispatcher=dispatcher) for h in dispatcher.handlers if h is not self)

    def handle(self, event, dispatcher):
        super(DefaultHandler, self).handle(event, dispatcher)
        raise StopDispatch


class MyInfoHandler(Handler):
    def __init__(self):
        super(MyInfoHandler, self).__init__()

    def check(self, event, dispatcher):
        return event.type is EventType.MY_INFO

    def handle(self, event, dispatcher):
        super(MyInfoHandler, self).handle(event, dispatcher)
        dispatcher.bot.uin = event.data["aimId"]
        dispatcher.bot.nick = event.data["nick"]


class MessageHandler(Handler):
    def __init__(self, filters=None, callback=None):
        super(MessageHandler, self).__init__(callback)

        self.filters = filters

    def check(self, event, dispatcher):
        return event.type in (EventType.IM, EventType.OFFLINE_IM) and bool(not self.filters or self.filters(event))


class UserAddedToBuddyListHandler(Handler):
    def check(self, event, dispatcher):
        return event.type is EventType.USER_ADDED_TO_BUDDY_LIST


class CommandHandler(MessageHandler):
    def __init__(self, command, filters=None, callback=None):
        super(CommandHandler, self).__init__(
            filters=MessageFilter.command if filters is None else AndFilter(MessageFilter.command, filters),
            callback=callback
        )

        self.command = command

    def check(self, event, dispatcher):
        return super(CommandHandler, self).check(event=event, dispatcher=dispatcher) and (not self.command or any(
            event.data["message"].partition(" ")[0][1:].lower() == c.lower() for c in (
                (self.command,) if isinstance(self.command, six.string_types) else self.command
            )
        ))


class HelpCommandHandler(CommandHandler):
    def __init__(self, filters=None, callback=None):
        super(HelpCommandHandler, self).__init__(command="help", filters=filters, callback=callback)


class FeedbackCommandHandler(CommandHandler):
    def __init__(
        self, target, message="Feedback from {source}: {message}", reply="Got it!", error_reply=None,
        command="feedback", filters=None
    ):
        super(FeedbackCommandHandler, self).__init__(command=command, filters=filters, callback=self.message_cb)

        self.target = target
        self.message = message
        self.reply = reply
        self.error_reply = error_reply

    def message_cb(self, bot, event):
        feedback_text = event.data["message"].partition(" ")[2].strip()
        if feedback_text:
            bot.send_im(target=self.target, message=self.message.format(
                source=event.data["source"]["aimId"], message=feedback_text
            ))

            if self.reply is not None:
                bot.send_im(target=event.data["source"]["aimId"], message=self.reply)
        elif self.error_reply is not None:
            bot.send_im(target=event.data["source"]["aimId"], message=self.error_reply)


class UnknownCommandHandler(MessageHandler):
    def __init__(self, filters=None, callback=None):
        super(UnknownCommandHandler, self).__init__(
            filters=MessageFilter.command if filters is None else AndFilter(MessageFilter.command, filters),
            callback=callback
        )

    def check(self, event, dispatcher):
        return super(UnknownCommandHandler, self).check(event=event, dispatcher=dispatcher) and not any(
            h.check(event=event, dispatcher=self) for h in dispatcher.handlers if isinstance(h, CommandHandler)
        )

    def handle(self, event, dispatcher):
        super(UnknownCommandHandler, self).handle(event, dispatcher)
        raise StopDispatch


class TypingHandler(Handler):
    def check(self, event, dispatcher):
        return event.type is EventType.TYPING


class SentIMHandler(Handler):
    def check(self, event, dispatcher):
        return event.type is EventType.SENT_IM


class WebRTCHandler(Handler):
    def check(self, event, dispatcher):
        return (
            super(WebRTCHandler, self).check(event=event, dispatcher=dispatcher) and
            event.type is EventType.WEBRTC_MSG
        )
