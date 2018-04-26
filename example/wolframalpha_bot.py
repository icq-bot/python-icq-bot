import cgi
import io
import logging.config
import random

import requests
from PIL import Image
from googletrans import Translator

from icq.bot import ICQBot, LoggingHTTPAdapter
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import (
    MessageHandler, FeedbackCommandHandler, UserAddedToBuddyListHandler, UnknownCommandHandler
)

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "WolframAlpha Bot"
VERSION = "1.0.1"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

WOLFRAM_BASE_URL = "https://api.wolframalpha.com"
WOLFRAM_APP_IDS = ("000000-0000000000", "000000-0000000000", "000000-0000000000", "000000-0000000000")
WOLFRAM_API_TIMEOUT_S = 25
WOLFRAM_HTTP_TIMEOUT_S = 30

TRANSLATOR = Translator()
for scheme in ("http://", "https://"):
    TRANSLATOR.session.mount(scheme, LoggingHTTPAdapter())


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(
        target=source,
        message="This is Wolfram|Alpha, the computational knowledge engine bot. Ask me any question, and i'll try to fi"
                "nd or calculate an answer for you.\n\nI offer two types of response depending on your query:\n1. Short"
                " text response - to get a short answer by Wolfram|Alpha end your query with a question sign.\n2. Detai"
                "led image response - to get an image of a complete Wolfram|Alpha result page use NO question sign at t"
                "he end of your query.\n\nIf your search returns no result, i'll try the other query type for you autom"
                "atically.\n\nFor more info and examples see: https://www.wolframalpha.com/examples/\n\nAvailable comma"
                "nds:\n/help - hint list\n/feedback your text here - leave feedback\n/stop - prevent bot from writing m"
                "essages\n/start - allow bot to write messages\n\n---\n\nЭто бот базы знаний и набора вычислительных ал"
                "горитмов Wolfram|Alpha. Можешь задать мне любой вопрос и я постараюсь найти или вычислить ответ.\n\nСу"
                "ществует два типа ответов в зависимости от запроса:\n1. Короткий текстовый ответ - чтобы получить коро"
                "ткий ответ от Wolfram|Alpha, поставь знак вопроса в конце запроса.\n2. Детальный графический ответ - ч"
                "тобы получить изображение полного ответа от Wolfram|Alpha, НЕ ставь знак вопроса в конце запроса.\n\nЕ"
                "сли ничего не было найдено по текущему типу запроса, я автоматически попробую найти ответ по другому т"
                "ипу запроса.\n\nБолее подробная информация с примерами: https://www.wolframalpha.com/examples/\n\nДост"
                "упные команды:\n/help - список подсказок\n/feedback здесь твой текст - отправить отзыв\n/stop - запрет"
                "ить боту присылать сообщения\n/start - разрешить боту присылать сообщения"
    )


def wolfram_question(session, text):
    return session.get(
        url="{}/v1/result".format(WOLFRAM_BASE_URL),
        params={
            "appid": random.choice(WOLFRAM_APP_IDS),
            "i": text,
            "units": "metric",
            "timeout": WOLFRAM_API_TIMEOUT_S
        },
        stream=True,
        timeout=WOLFRAM_HTTP_TIMEOUT_S
    )


def wolfram_simple(session, text):
    return session.get(
        url="{}/v1/simple".format(WOLFRAM_BASE_URL),
        params={
            "appid": random.choice(WOLFRAM_APP_IDS),
            "i": text,
            "layout": "labelbar",
            "background": "white",
            "foreground": "black",
            "units": "metric",
            "timeout": WOLFRAM_API_TIMEOUT_S
        },
        timeout=WOLFRAM_HTTP_TIMEOUT_S
    )


def search_cb(bot, event):
    source = event.data["source"]["aimId"]

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    message = event.data["message"].strip()
    wolfram_query = wolfram_question if message.endswith("?") else wolfram_simple

    # todo: fail for "lim z->2pi (sinz/z)" or "i25" - need to first query WolframAlpha before translation.

    translated = None
    # noinspection PyBroadException
    try:
        translated = TRANSLATOR.translate(text=message, dest="en")
        message = translated.text
    except Exception:
        log.exception("Failed to translate message!")

    wolfram_response = wolfram_query(session=bot.http_session, text=message)
    if wolfram_response.status_code == requests.codes.not_implemented:
        wolfram_query = wolfram_question if wolfram_query is wolfram_simple else wolfram_simple
        wolfram_response = wolfram_query(session=bot.http_session, text=message)

    if wolfram_response.status_code == requests.codes.ok:
        mime_type = cgi.parse_header(wolfram_response.headers.get("Content-Type", ""))[0]
        if mime_type.split("/")[0] == "image":
            with io.BytesIO(wolfram_response.content) as image_in, io.BytesIO() as image_out:
                Image.open(image_in).save(image_out, "PNG")
                image_out.seek(0)

                upload_response = bot.send_file(file=image_out, name="image.png")
                file_url = upload_response.json()["data"]["static_url"]

                bot.send_im(target=source, message=file_url)
        elif mime_type == "text/plain":
            response_text = wolfram_response.text

            if translated and translated.src != "en":
                # noinspection PyBroadException
                try:
                    response_text = TRANSLATOR.translate(text=response_text, dest=translated.src).text
                except Exception:
                    log.exception("Failed to translate response!")

            bot.send_im(target=source, message=response_text)
    elif wolfram_response.status_code == requests.codes.not_implemented:
        bot.send_im(
            target=source,
            message="Nothing found, try to search something else.\n---\nНичего не найдено, попробуй поискать что-нибудь"
                    " ещё."
        )
    else:
        bot.send_im(
            target=source,
            message="Something has gone wrong, try again later.\n---\nЧто-то пошло не так, попробуй ещё позже."
        )

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text, callback=search_cb))
    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER, reply="Got it!\n---\nПринято!"))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.message & ~(MessageFilter.text | MessageFilter.command),
        callback=help_cb,
    ))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
