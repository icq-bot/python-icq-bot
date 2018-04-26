import logging.config
import re

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import (
    UnknownCommandHandler, UserAddedToBuddyListHandler, MessageHandler, DefaultHandler, FeedbackCommandHandler,
    HelpCommandHandler, TypingHandler
)
from icq.util import decode_file_id

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Test Bot"
VERSION = "0.0.0"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"


def help_cb(bot, event):
    source = event.data["source"]["aimId"]
    (command, command_body) = event.data["message"].partition(" ")[::2]
    bot.send_im(
        target=source,
        message="Command '{message}' with body '{command_body}' received from '{source}'.".format(
            source=source, message=command[1:], command_body=command_body
        )
    )


def unknown_command_cb(bot, event):
    source = event.data["source"]["aimId"]
    (command, command_body) = event.data["message"].partition(" ")[::2]
    bot.send_im(
        target=source,
        message="Unknown command '{message}' with body '{command_body}' received from '{source}'.".format(
            source=source, message=command[1:], command_body=command_body
        )
    )


def user_added_cb(bot, event):
    source = event.data["requester"]
    bot.send_im(target=source, message="User '{source}' added bot to buddy list.".format(source=source))


def typing_cb(bot, event):
    source = event.data["aimId"]
    bot.send_im(target=source, message="Typing status '{typing_status}' received from user {source}.".format(
        source=source, typing_status=TypingStatus(event.data["typingStatus"]).value
    ))


def text_cb(bot, event):
    source = event.data["source"]["aimId"]
    bot.send_im(target=source, message="Text '{message}' received from '{source}'.".format(
        source=source, message=event.data["message"]
    ))


def sticker_cb(bot, event):
    source = event.data["source"]["aimId"]
    bot.send_im(target=source, message="Sticker '{sticker}' received from '{source}'.".format(
        source=source, sticker=event.data["stickerId"]
    ))


def url_cb(bot, event):
    source = event.data["source"]["aimId"]
    bot.send_im(target=source, message="URL '{url}' received from '{source}'.".format(
        source=source, url=event.data["message"]
    ))


def image_cb(bot, event):
    source = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source,
        message="Image '{image}' (size is '{width}x{height}') received from '{source}'.".format(
            source=source, image=event.data["message"], width=file_meta.width, height=file_meta.height
        )
    )


def video_cb(bot, event):
    source = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source,
        message="Video '{video}' (size is '{width}x{height}') received from '{source}'.".format(
            source=source, video=event.data["message"], width=file_meta.width, height=file_meta.height
        )
    )


def audio_cb(bot, event):
    source = event.data["source"]["aimId"]
    file_meta = decode_file_id(
        re.search(MessageFilter._FileFilter.FILE_URL_REGEXP, event.data["message"].strip()).group("file_id")
    )
    bot.send_im(
        target=source,
        message="Audio '{audio}' (length is '{length}') received from '{source}'.".format(
            source=source, audio=event.data["message"], length=file_meta.length
        )
    )


def chat_cb(bot, event):
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


def default_cb(bot, event):
    log.debug("Default callback triggered for event type '{}'.".format(event.type))


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(HelpCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=unknown_command_cb))
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(user_added_cb))
    bot.dispatcher.add_handler(TypingHandler(typing_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text, callback=text_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.sticker, callback=sticker_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.url, callback=url_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.image, callback=image_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.video, callback=video_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.audio, callback=audio_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.chat, callback=chat_cb))
    bot.dispatcher.add_handler(DefaultHandler(default_cb))

    # Registering command handlers.
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
