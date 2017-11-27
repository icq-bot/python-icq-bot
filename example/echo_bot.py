import logging.config

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import TypingHandler, MessageHandler, CommandHandler, UnknownCommandHandler, FeedbackCommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Echo Bot"
VERSION = "1.0.0"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"


def help_callback(bot, event):
    log.debug("Command 'help' received, replying.")
    bot.send_im(target=event.data["source"]["aimId"], message="I'm at your service!")


def status_callback(bot, event):
    log.debug("Command 'status' received, replying.")
    bot.send_im(
        target=event.data["source"]["aimId"], message="https://files.icq.net/get/05k5r12erfSSAgyt09sNgH5a11d7cc1aj"
    )


def typing_callback(bot, event):
    log.debug("Typing received, echoing with the same typing status.")
    bot.set_typing(target=event.data["aimId"], typing_status=TypingStatus(event.data["typingStatus"]))


def message_callback(bot, event):
    log.debug("Message received, echoing with the same message.")

    source_uin = event.data["source"]["aimId"]
    if "stickerId" in event.data:
        bot.send_sticker(target=source_uin, sticker_id=event.data["stickerId"])
    else:
        bot.send_im(target=source_uin, message=event.data["message"])


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(TypingHandler(typing_callback))
    bot.dispatcher.add_handler(MessageHandler(
        callback=message_callback, filters=MessageFilter.text | MessageFilter.sticker
    ))

    # Registering command handlers.
    bot.dispatcher.add_handler(CommandHandler(callback=help_callback, command="help"))
    bot.dispatcher.add_handler(CommandHandler(callback=status_callback, command="status"))
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))
    bot.dispatcher.add_handler(UnknownCommandHandler(message_callback))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
