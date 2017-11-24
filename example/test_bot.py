import logging.config
import re

from icq.bot import ICQBot
from icq.filter import MessageFilter
from icq.handler import MessageHandler, UserAddedToBuddyListHandler, CommandHandler, FeedbackCommandHandler
from icq.util import decode_file_id

NAME = "Test Bot"
VERSION = "0.0.0"
TOKEN = "000.0000000000.0000000000:000000000"

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)


def command_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    bot.send_im(target=source_uin, message="Command '{message}' received from '{source_uin}'.".format(
        source_uin=source_uin, message=event.data["message"]
    ))


def user_added_callback(bot, event):
    source_uin = event.data["requester"]
    bot.send_im(target=source_uin, message="User '{source_uin}' added bot to buddy list.".format(source_uin=source_uin))


def text_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    bot.send_im(target=source_uin, message="Text '{message}' received from '{source_uin}'.".format(
        source_uin=source_uin, message=event.data["message"]
    ))


def sticker_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    bot.send_im(target=source_uin, message="Sticker '{sticker}' received from '{source_uin}'.".format(
        source_uin=source_uin, sticker=event.data["stickerId"]
    ))


def link_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    bot.send_im(target=source_uin, message="Link '{link}' received from '{source_uin}'.".format(
        source_uin=source_uin, link=event.data["message"]
    ))


def image_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source_uin,
        message="Image '{image}' (size is '{width}x{height}') received from '{source_uin}'.".format(
            source_uin=source_uin, image=event.data["message"], width=file_meta.width, height=file_meta.height
        )
    )


def video_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source_uin,
        message="Video '{video}' (size is '{width}x{height}') received from '{source_uin}'.".format(
            source_uin=source_uin, video=event.data["message"], width=file_meta.width, height=file_meta.height
        )
    )


def audio_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source_uin,
        message="Audio '{audio}' (length is '{length}') received from '{source_uin}'.".format(
            source_uin=source_uin, audio=event.data["message"], length=file_meta.length
        )
    )


def chat_callback(bot, event):
    chat_attributes = event.data["MChat_Attrs"]
    bot.send_im(
        target=event.data["source"]["aimId"],
        message="Received chat message attributes are: sender is '{sender}', sender name is '{sender_name}', chat name "
                "is '{chat_name}'.".format(
            sender=chat_attributes["sender"],
            sender_name=chat_attributes["senderName"],
            chat_name=chat_attributes["chat_name"]
        )
    )


def main():
    # Creating new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering required handlers for messages.
    bot.dispatcher.add_handler(CommandHandler(callback=command_callback))
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(callback=user_added_callback))
    bot.dispatcher.add_handler(MessageHandler(callback=text_callback, filters=MessageFilter.text))
    bot.dispatcher.add_handler(MessageHandler(callback=sticker_callback, filters=MessageFilter.sticker))
    bot.dispatcher.add_handler(MessageHandler(callback=link_callback, filters=MessageFilter.link))
    bot.dispatcher.add_handler(MessageHandler(callback=image_callback, filters=MessageFilter.image))
    bot.dispatcher.add_handler(MessageHandler(callback=video_callback, filters=MessageFilter.video))
    bot.dispatcher.add_handler(MessageHandler(callback=audio_callback, filters=MessageFilter.audio))
    bot.dispatcher.add_handler(MessageHandler(callback=chat_callback, filters=MessageFilter.chat))

    bot.dispatcher.add_handler(FeedbackCommandHandler(command="fb", target="176756440"))

    # Starting polling thread watching for new events from server. This is non-blocking call.
    bot.start_polling()

    # Block current thread while bot working until SIGINT, SIGTERM or SIGABRT received.
    bot.idle()


if __name__ == "__main__":
    main()
