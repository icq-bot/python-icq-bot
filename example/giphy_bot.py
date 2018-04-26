import logging.config
import random

from alphabet_detector import AlphabetDetector
from googletrans import Translator
from transliterate import translit

from icq.bot import ICQBot, LoggingHTTPAdapter
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import (
    MessageHandler, FeedbackCommandHandler, UserAddedToBuddyListHandler, UnknownCommandHandler, CommandHandler
)

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Giphy Bot"
VERSION = "1.0.2"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

GIPHY_BASE_URL = "https://api.giphy.com"
GIPHY_KEYS = ("00000000000000000000000000000000", "00000000000000000000000000000000")
GIPHY_HTTP_TIMEOUT_S = 30
GIPHY_TRENDING_LIMIT = 100  # How many items we should query from Giphy for each user "trending" request.
GIPHY_TRENDING_SIZE = 3  # How many random items we should send to user for each "trending" request.
GIPHY_SEARCH_LIMIT = 20  # How many items we should query from Giphy for each user "search" request.
GIPHY_SEARCH_SIZE = 1  # How many random items we should send to user for each "search" request.

TRANSLATOR = Translator()
for scheme in ("http://", "https://"):
    TRANSLATOR.session.mount(scheme, LoggingHTTPAdapter())


class LanguageByAlphabetDetector(object):
    _alphabet_detector = AlphabetDetector()

    _mapping = {
        _alphabet_detector.is_greek: "el",
        _alphabet_detector.is_cyrillic: "ru",
        _alphabet_detector.is_arabic: "ar",
        _alphabet_detector.is_hebrew: "iw",
        _alphabet_detector.is_cjk: "zh",
        _alphabet_detector.is_hangul: "ko",
        _alphabet_detector.is_hiragana: "ja",
        _alphabet_detector.is_katakana: "ja",
        _alphabet_detector.is_thai: "th"
    }

    @staticmethod
    def guess_language(text):
        for (check_function, code) in LanguageByAlphabetDetector._mapping.items():
            if check_function(text):
                return code


language_detector = LanguageByAlphabetDetector()


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(
        target=source,
        message="Send me a text of your choice to get a related cool gif {cool}\n\n/random - a random gif\n/trending - "
                "a bunch of random TOP-100 gifs\n/help - hint list\n/feedback your text here - leave feedback\n\n---\n"
                "\nПришли мне любой текст, и я подберу подходящую гифку {cool}\n\n/random - случайная гифка\n/trending "
                "- несколько случайных гифок из ТОП-100\n/help - список подсказок\n/feedback здесь твой текст - отправи"
                "ть отзыв".format(cool=random.choice("👻👍🤘👌"))
    )


def giphy_search(session, text, language):
    return session.get(
        url="{}/v1/gifs/search".format(GIPHY_BASE_URL),
        params={
            "api_key": random.choice(GIPHY_KEYS),
            "fmt": "json",
            "limit": GIPHY_SEARCH_LIMIT,
            "q": text,
            "lang": language
        },
        timeout=GIPHY_HTTP_TIMEOUT_S
    )


def search_cb(bot, event):
    source = event.data["source"]["aimId"]

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    message = event.data["message"].strip()

    # noinspection PyBroadException
    try:
        language = TRANSLATOR.detect(message).lang[-2:]
    except Exception:
        log.exception("Failed to detect language!")
        language = language_detector.guess_language(message)

    data = giphy_search(session=bot.http_session, text=message, language=language).json()["data"]
    if not data:
        # Not found in the original language, let's re-try in English.
        # noinspection PyBroadException
        try:
            text = TRANSLATOR.translate(text=message, dest="en").text
        except Exception:
            log.exception("Failed to translate message!")
        else:
            data = giphy_search(session=bot.http_session, text=text, language="en").json()["data"]

        if not data:
            # noinspection PyBroadException
            try:
                text = translit(value=message, reversed=True)
            except Exception:
                log.exception("Failed to transliterate message!")
            else:
                data = giphy_search(session=bot.http_session, text=text, language="en").json()["data"]

    if data:
        for gif in random.sample(data, min(GIPHY_SEARCH_SIZE, len(data))):
            bot.send_im(target=source, message=gif["images"]["original"]["url"])
    else:
        bot.send_im(
            target=source,
            message="Nothing found, this doesn't make any sense {face}\n---\nНичего не найдено, ерунда какая-то "
                    "{face}".format(face=random.choice("😜🤔🤥😐😬🤐🤦"))
        )

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def giphy_random(session):
    return session.get(
        url="{}/v1/gifs/random".format(GIPHY_BASE_URL),
        params={
            "api_key": random.choice(GIPHY_KEYS),
            "fmt": "json"
        },
        timeout=GIPHY_HTTP_TIMEOUT_S
    )


def random_cb(bot, event):
    source = event.data["source"]["aimId"]

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    data = giphy_random(bot.http_session).json()["data"]

    bot.send_im(target=source, message=data["image_original_url"])

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def giphy_trending(session):
    return session.get(
        url="{}/v1/gifs/trending".format(GIPHY_BASE_URL),
        params={
            "api_key": random.choice(GIPHY_KEYS),
            "fmt": "json",
            "limit": GIPHY_TRENDING_LIMIT
        },
        timeout=GIPHY_HTTP_TIMEOUT_S
    )


def trending_cb(bot, event):
    source = event.data["source"]["aimId"]

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    data = giphy_trending(bot.http_session).json()["data"]

    for gif in random.sample(data, GIPHY_TRENDING_SIZE):
        bot.send_im(target=source, message=gif["images"]["original"]["url"])

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text, callback=search_cb))
    bot.dispatcher.add_handler(CommandHandler(command="random", callback=random_cb))
    bot.dispatcher.add_handler(CommandHandler(command="trending", callback=trending_cb))
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER, reply="Got it!\n---\nПринято!"))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.message & ~(MessageFilter.text | MessageFilter.command), callback=help_cb
    ))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
