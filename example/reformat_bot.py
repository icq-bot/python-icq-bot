import ast
import json
import logging.config
import re
from io import StringIO, BytesIO

from lxml import etree

from icq.bot import ICQBot
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import MessageHandler, UserAddedToBuddyListHandler, FeedbackCommandHandler, \
    HelpCommandHandler, UnknownCommandHandler, CommandHandler

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Reformat Bot"
VERSION = "0.0.4"
TOKEN = "000.0000000000.0000000000:000000000"
OWNER = "000000000"

TEXT_RESPONSE_LIMIT = 10000

FORMAT_INDENT = 4


def help_cb(bot, event):
    source = event.data.get("requester") or event.data["source"]["aimId"]
    bot.send_im(
        target=source,
        message="Send me a text or a text file and i'll make pretty format for you. Also you can send me several data s"
                "tructures for reformatting, each on a new line. The supported formats are: JSON, PLSN, HTML and XML.\n"
                "\nAvailable commands:\n/help - hint list\n/feedback your text here - leave feedback\n/stop - prevent b"
                "ot from writing messages\n/start - allow bot to write messages"
    )


def reformat_json(text):
    if not text.startswith(("{", "[")):
        raise ValueError

    try:
        return json.dumps(json.loads(text), indent=FORMAT_INDENT)
    except ValueError as e:
        return "Error while parsing JSON: {}".format(str(e))


PLSN_REGEXP = re.compile(r"^(?:[0-9]+(?:\.[0-9]+)?|[([{]+)$")


def reformat_plsn(text):
    if not PLSN_REGEXP.match(text):
        raise ValueError

    try:
        return json.dumps(ast.literal_eval(text), indent=FORMAT_INDENT, sort_keys=True)
    except (ValueError, SyntaxError) as e:
        return "Error while parsing PLSN: {}".format(str(e))


def reformat_xml(text):
    if not text.startswith("<"):
        raise ValueError

    parser = etree.XMLParser(recover=False)
    tree = etree.parse(BytesIO(text.encode("utf-8")), parser)
    return etree.tostring(tree.getroot(), encoding="unicode", pretty_print=True)


def reformat_html(text):
    if not text.startswith("<"):
        raise ValueError

    parser = etree.HTMLParser(recover=False)
    tree = etree.parse(StringIO(text), parser)
    return etree.tostring(tree.getroot(), encoding="unicode", pretty_print=True)


def reformat_cb(bot, event):
    source = event.data["source"]["aimId"]
    message = event.data["message"].strip()

    bot.set_typing(target=source, typing_status=TypingStatus.TYPING)

    for func in (reformat_json, reformat_plsn, reformat_xml, reformat_html):
        # noinspection PyBroadException
        try:
            result = []
            for token in filter(None, message.split(sep="\n")):
                result.append(func(token))
            message = "\n".join(result)
            break
        except Exception:
            log.exception("Exception while trying {}!".format(func.__name__))

    if len(message) > TEXT_RESPONSE_LIMIT:
        upload_response = bot.send_file(file=message, name="formatted.json")
        message = upload_response.json()["data"]["static_url"]

    bot.send_im(target=source, message=message)

    bot.set_typing(target=source, typing_status=TypingStatus.NONE)


def json_cb():
    pass


def json_escape_cb():
    pass


def plsn_cb():
    pass


def html_cb():
    pass


def xml_cb():
    pass


def file_cb(bot, event):
    event.data["message"] = bot.download_file(event.data["message"]).text
    reformat_cb(bot, event)


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering handlers.
    bot.dispatcher.add_handler(UserAddedToBuddyListHandler(help_cb))
    bot.dispatcher.add_handler(HelpCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(UnknownCommandHandler(callback=help_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.message & ~(MessageFilter.command | MessageFilter.text | MessageFilter.file),
        callback=help_cb
    ))

    bot.dispatcher.add_handler(MessageHandler(filters=MessageFilter.text, callback=reformat_cb))
    bot.dispatcher.add_handler(MessageHandler(
        filters=MessageFilter.file & ~(MessageFilter.image | MessageFilter.video | MessageFilter.audio),
        callback=file_cb
    ))

    bot.dispatcher.add_handler(CommandHandler(command="json", callback=json_cb))
    bot.dispatcher.add_handler(CommandHandler(command=("json_escape", "jsonescape"), callback=json_escape_cb))
    bot.dispatcher.add_handler(CommandHandler(command="plsn", callback=plsn_cb))
    bot.dispatcher.add_handler(CommandHandler(command="html", callback=html_cb))
    bot.dispatcher.add_handler(CommandHandler(command="xtml", callback=xml_cb))

    bot.dispatcher.add_handler(FeedbackCommandHandler(target=OWNER))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
