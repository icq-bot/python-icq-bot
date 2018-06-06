import logging.config

from icq.bot import ICQBot
from icq.constant import MChatMethod
from icq.filter import MessageFilter
from icq.handler import UnknownCommandHandler, MessageHandler, UserAddedToBuddyListHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Chat ID Bot"
VERSION = "0.0.1"
TOKEN = "000.0000000000.0000000000:000000000"


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(target=source, message="Add me to your chat and i'll tell you its ID.")


def chat_cb(bot, event):
    chat_id = event.data["source"]["aimId"]
    source_uin = event.data["MChat_Attrs"]["sender"]
    mchat_method = event.data["MChat_Attrs"].get("method")

    if mchat_method == MChatMethod.INVITE.value:
        chat_info = bot.get_chat_info(sn=chat_id).json()
        bot.remove_buddy(buddy=chat_id)
        bot.send_im(target=source_uin, message="Chat \"{chat}\" has ID \"{id}\".".format(
            chat=chat_info["results"]["name"],
            id=chat_id
        ))
        return

    bot.send_im(target=event.data["source"]["aimId"], message="")


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.message & ~(MessageFilter.command | MessageFilter.chat), callback=help_cb
    ))

    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.chat, callback=chat_cb))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
