import hashlib
import logging.config
import re
from base64 import b64encode
from hmac import HMAC

from oauthlib.oauth1.rfc5849 import signature

from icq.bot import ICQBot
from icq.filter import MessageFilter
from icq.handler import (
    HelpCommandHandler, MessageHandler, UnknownCommandHandler, FeedbackCommandHandler
)

try:
    from urllib import parse as urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "OAuth Bot"
VERSION = "1.0.2"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

HTTP_METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"}


def help_cb(bot, event):
    source = event.data["source"]["aimId"]
    bot.send_im(target=source, message="You can send me:\n- URL\n- URL method\n- URL method secret")


def message_cb(bot, event):
    source = event.data["source"]["aimId"]
    message = event.data["message"]

    method = url = query = secret_key = None
    for token in re.split(pattern=r"\s+", string=message):
        if method is None and token.upper() in HTTP_METHODS:
            method = token
            continue

        if url is None:
            try:
                parsed = urlparse.urlparse(url=token)
                assert parsed.scheme and parsed.netloc
                url = token
                query = parsed.query
                continue
            except (ValueError, AssertionError):
                pass

        if secret_key is None:
            secret_key = token

    if url is None or query is None:
        help_cb(bot=bot, event=event)
        return

    if method is None:
        method = "METHOD"

    params = urlparse.parse_qsl(query, keep_blank_values=True)
    normalized_params = signature.normalize_parameters(params)
    normalized_url = signature.normalize_base_string_uri(url)
    sign_base = signature.construct_base_string(method, normalized_url, normalized_params)

    sign = None
    if secret_key is not None:
        sign = b64encode(HMAC(secret_key.encode(), sign_base.encode(), hashlib.sha256).digest()).decode()

    bot.send_im(
        target=source,
        message="Signature base: {signature_base}{sign}".format(
            signature_base=sign_base, sign="" if sign is None else "\n\nSignature: {sign}".format(sign=sign)
        )
    )


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(HelpCommandHandler())  # /setpassover is false for this bot.
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.sticker, callback=help_cb))

    bot.dispatcher.add_handler(MessageHandler(
        filters=~(MessageFilter.command | MessageFilter.sticker), callback=message_cb
    ))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=message_cb))

    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
