import json
import logging.config

import apiai

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import UnknownCommandHandler, UserAddedToBuddyListHandler, MessageHandler, FeedbackCommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Dialogflow Bot"
VERSION = "0.0.2"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

DF_TOKEN = "00000000000000000000000000000000"
DF_API = apiai.ApiAI(DF_TOKEN)


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(target=source, message="Добро пожаловать в мир ИИ! Давай поговорим о чём-нибудь.")


def message_cb(bot, event):
    source = event.data["source"]["aimId"]

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    request = DF_API.text_request()
    request.lang = "ru"
    request.session_id = source
    request.query = event.data["message"]
    response_json = json.loads(request.getresponse().read().decode("utf-8"))
    response_text = response_json["result"]["fulfillment"]["speech"]

    bot.send_im(
        target=source,
        message=response_text if response_text else "Извини, я ничего не понял..."
    )

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.message & ~(MessageFilter.text | MessageFilter.command), callback=help_cb
    ))

    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text, callback=message_cb))

    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER, reply="Принято!"))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
