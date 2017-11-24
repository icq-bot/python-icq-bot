import logging.config
import random
import sys

from icq.bot import ICQBot

NAME = "Nikodim Bot"
VERSION = "0.0.1"
TOKEN = "000.0000000000.0000000000:000000000"

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

TRANSLATE = {
    "привет": ("гой еси", "радуйся", "здрав будь"),
    "пока": ("доброго пути", "ну, будь", "бывай")

}


def process(message):
    for (old, new) in TRANSLATE.items():
        message = message.replace(old, random.choice(new))
    return message


def main():
    log.info("Starting bot.")

    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    while True:
        try:
            response = bot.fetch_events()
            for event in response.json()["response"]["data"]["events"]:
                if event["type"] == "im":
                    event_data = event["eventData"]
                    source_uin = event_data["source"]["aimId"]
                    message = event_data["message"]
                    if "stickerId" not in event_data:
                        bot.send_im(target=source_uin, message=process(message))
        except KeyboardInterrupt:
            log.info("Shutting down bot.")
            sys.exit()
        except:
            log.exception("Exception in main loop!")


if __name__ == '__main__':
    main()
