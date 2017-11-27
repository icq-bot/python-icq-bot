import logging.config

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import MessageHandler, UnknownCommandHandler

try:
    from urllib import parse
except ImportError:
    import urlparse as parse

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "URL Encode Bot"
VERSION = "1.0.0"
TOKEN = "000.0000000000.0000000000:000000000"


def message_callback(bot, event):
    log.debug("Message received, replying.")

    source_uin = event.data["source"]["aimId"]
    try:
        bot.set_typing(target=source_uin, typing_status=TypingStatus.TYPING)
        bot.send_im(target=source_uin, message=parse.quote_plus(event.data["message"]))
    finally:
        bot.set_typing(target=source_uin, typing_status=TypingStatus.NONE)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(MessageHandler(callback=message_callback, filters=MessageFilter.text))

    # Registering command handlers.
    bot.dispatcher.add_handler(UnknownCommandHandler(message_callback))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
