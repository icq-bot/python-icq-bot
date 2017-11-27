import logging.config
import re

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import (
    CommandHandler, UnknownCommandHandler, UserAddedToBuddyListHandler, TypingHandler, MessageHandler, DefaultHandler,
    FeedbackCommandHandler,
)
from icq.util import decode_file_id

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Test Bot"
VERSION = "0.0.0"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"


def help_command_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    (command, command_body) = event.data["message"].partition(" ")[::2]
    bot.send_im(
        target=source_uin,
        message="Command '{message}' with body '{command_body}' received from '{source_uin}'.".format(
            source_uin=source_uin, message=command[1:], command_body=command_body
        )
    )


def unknown_command_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    (command, command_body) = event.data["message"].partition(" ")[::2]
    bot.send_im(
        target=source_uin,
        message="Unknown command '{message}' with body '{command_body}' received from '{source_uin}'.".format(
            source_uin=source_uin, message=command[1:], command_body=command_body
        )
    )


def user_added_callback(bot, event):
    source_uin = event.data["requester"]
    bot.send_im(target=source_uin, message="User '{source_uin}' added bot to buddy list.".format(source_uin=source_uin))


def typing_callback(bot, event):
    source_uin = event.data["aimId"]
    bot.send_im(target=source_uin, message="Typing status '{typing_status}' received from user {source_uin}.".format(
        source_uin=source_uin, typing_status=TypingStatus(event.data["typingStatus"]).value
    ))


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


def url_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    bot.send_im(target=source_uin, message="URL '{url}' received from '{source_uin}'.".format(
        source_uin=source_uin, url=event.data["message"]
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


def default_callback(bot, event):
    log.debug("Default callback triggered for event type '{}'.".format(event.event_type))


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(CommandHandler(callback=help_command_callback, command="help"))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=unknown_command_callback))
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(callback=user_added_callback))
    bot.dispatcher.add_handler(TypingHandler(callback=typing_callback))
    bot.dispatcher.add_handler(MessageHandler(callback=text_callback, filters=MessageFilter.text))
    bot.dispatcher.add_handler(MessageHandler(callback=sticker_callback, filters=MessageFilter.sticker))
    bot.dispatcher.add_handler(MessageHandler(callback=url_callback, filters=MessageFilter.url))
    bot.dispatcher.add_handler(MessageHandler(callback=image_callback, filters=MessageFilter.image))
    bot.dispatcher.add_handler(MessageHandler(callback=video_callback, filters=MessageFilter.video))
    bot.dispatcher.add_handler(MessageHandler(callback=audio_callback, filters=MessageFilter.audio))
    bot.dispatcher.add_handler(MessageHandler(callback=chat_callback, filters=MessageFilter.chat))
    bot.dispatcher.add_handler(DefaultHandler(callback=default_callback))

    # Registering command handlers.
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
