import logging.config
import random
from time import sleep

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import MessageHandler, UnknownCommandHandler, HelpCommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Meme Bot"
VERSION = "1.0.1"
TOKEN = "000.0000000000.0000000000:000000000"


def message_cb(bot, event):
    log.debug("Message received, replying.")

    source = event.data["source"]["aimId"]
    try:
        bot.set_typing(target=source, typing_status=TypingStatus.TYPING)
        bot.send_sticker(target=source, sticker_id="ext:95:sticker:" + str(random.randint(1, 25)))
        sleep(random.randint(3, 5))
        bot.send_im(target=source, message="https://icq.com/people/70003")
    finally:
        bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def help_cb(bot, event):
    log.debug("Command 'help' received, replying.")
    bot.send_sticker(target=event.data["source"]["aimId"], sticker_id="ext:95:sticker:6")


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text | MessageFilter.sticker, callback=message_cb))

    # Registering command handlers.
    bot.dispatcher.add_handler(HelpCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=message_cb))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
