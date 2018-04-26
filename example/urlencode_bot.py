import logging.config

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import (
    MessageHandler, UnknownCommandHandler, UserAddedToBuddyListHandler, HelpCommandHandler, FeedbackCommandHandler
)

try:
    from urllib import parse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse as parse

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "URL Encode Bot"
VERSION = "1.0.3"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(
        target=source,
        message="I'll help help you to make URL-encode of any posted text.\n\nAvailable commands:\n/help - hint list\n/"
                "feedback your text here - leave feedback\n/stop - prevent bot from writing messages\n/start - allow bo"
                "t to write messages"
    )


def message_cb(bot, event):
    source = event.data["source"]["aimId"]
    try:
        bot.set_typing(target=source, typing_status=TypingStatus.TYPING)
        bot.send_im(target=source, message=parse.quote_plus(event.data["message"]))
    finally:
        bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(HelpCommandHandler(callback=help_cb))

    bot.dispatcher.add_handler(MessageHandler(filters=~MessageFilter.command, callback=message_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=message_cb))

    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
