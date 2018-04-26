import hashlib
import logging.config

from icq.bot import ICQBot
from icq.filter import MessageFilter
from icq.handler import (
    MessageHandler, UnknownCommandHandler, HelpCommandHandler, FeedbackCommandHandler
)

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Hash Bot"
VERSION = "1.0.2"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

BUFFER_SIZE = 4096


def message_cb(bot, event):
    source = event.data["source"]["aimId"]
    message = event.data["message"]

    message_bytes = message.encode()
    bot.send_im(
        target=source,
        message=(
            "SHA-1: {sha_1}\n\nSHA-224: {sha_224}\n\nSHA-256: {sha_256}\n\nSHA-384: {sha_384}\n\nSHA-512: {sha_512}\n\n"
            "MD5: {md5}"
        ).format(
            sha_1=hashlib.sha1(message_bytes).hexdigest(),
            sha_224=hashlib.sha224(message_bytes).hexdigest(),
            sha_256=hashlib.sha256(message_bytes).hexdigest(),
            sha_384=hashlib.sha384(message_bytes).hexdigest(),
            sha_512=hashlib.sha512(message_bytes).hexdigest(),
            md5=hashlib.md5(message_bytes).hexdigest()
        )
    )


def file_cb(bot, event):
    source = event.data["source"]["aimId"]
    message = event.data["message"]

    sha_1 = hashlib.sha1()
    sha_224 = hashlib.sha224()
    sha_256 = hashlib.sha256()
    sha_384 = hashlib.sha384()
    sha_512 = hashlib.sha512()
    md5 = hashlib.md5()

    file = bot.download_file(message)
    for chunk in file.iter_content(chunk_size=BUFFER_SIZE):
        sha_1.update(chunk)
        sha_224.update(chunk)
        sha_256.update(chunk)
        sha_384.update(chunk)
        sha_512.update(chunk)
        md5.update(chunk)

    bot.send_im(
        target=source,
        message=(
            "SHA-1: {sha_1}\n\nSHA-224: {sha_224}\n\nSHA-256: {sha_256}\n\nSHA-384: {sha_384}\n\nSHA-512: {sha_512}\n\n"
            "MD5: {md5}"
        ).format(
            sha_1=sha_1.hexdigest(),
            sha_224=sha_224.hexdigest(),
            sha_256=sha_256.hexdigest(),
            sha_384=sha_384.hexdigest(),
            sha_512=sha_512.hexdigest(),
            md5=md5.hexdigest()
        )
    )


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(HelpCommandHandler())  # /setpassover is false for this bot.

    bot.dispatcher.add_handler(MessageHandler(
        filters=~(MessageFilter.command | MessageFilter.file), callback=message_cb
    ))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.file, callback=file_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=message_cb))

    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
