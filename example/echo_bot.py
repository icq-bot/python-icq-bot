import logging.config

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import TypingHandler, MessageHandler, CommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Echo Bot"
VERSION = "1.0.4"
TOKEN = "000.0000000000.0000000000:000000000"


def status_cb(bot, event):
    log.debug("Command 'status' received, replying.")

    bot.send_im(
        target=event.data["source"]["aimId"], message="https://files.icq.net/get/05k5r12erfSSAgyt09sNgH5a11d7cc1aj"
    )


def typing_cb(bot, event):
    log.debug("Typing received, echoing with the same typing status.")

    bot.set_typing(target=event.data["aimId"], typing_status=TypingStatus(event.data["typingStatus"]))


def message_cb(bot, event):
    log.debug("Message received, echoing with the same message.")

    source = event.data["source"]["aimId"]
    bot.send_im(target=source, message=event.data["message"])


def sticker_cb(bot, event):
    log.debug("Sticker received, echoing with the same sticker.")

    source = event.data["source"]["aimId"]
    bot.send_sticker(target=source, sticker_id=event.data["stickerId"])


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(TypingHandler(typing_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.message, callback=message_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.sticker, callback=sticker_cb))

    # Registering command handlers.
    bot.dispatcher.add_handler(CommandHandler(command="status", callback=status_cb))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
