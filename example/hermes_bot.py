import logging.config
import random
import re
import sys
from abc import ABCMeta
from collections import defaultdict
from datetime import datetime

import requests

from icq.bot import ICQBot
from icq.constant import TypingStatus

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

NAME = "Hermes Bot"
VERSION = "0.0.1"
TOKEN = "000.0000000000.0000000000:000000000"

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

PHRASES = (
    "Sweet lion of Zion!", "Sweet manatee of Galilee!", "Sweet llamas of the Bahamas!",
    "Sweet something... of... someplace...", "Great cow of Moscow!", "Sweet giant anteater of Santa Anita!",
    "Sweet ghost of Babylon!", "Sacred boa of West and Eastern Samoa!", "Sacred hog of Prague!",
    "Cursed bacteria of Liberia!", "Sweet guinea pig of Winnipeg!", "Great bonda of Uganda!",
    "Sweet three-toed sloth of the ice planet Hoth!", "Sweet honey bee of infinity!",
    "Sweet yeti of the Serengeti!", "Sweet bongo of the Congo!", "Sweet squid of Madrid!",
    "Sweet kookaburra of Edinburgh!", "Sweet topology of cosmology!", "Sweet coincidence of Port-au-Prince!",
    "Sweet orca of Mallorca!", "Sweet candelabra of Le Havre, LaBarbara!"
)


class LogRecord(object):
    __metaclass__ = ABCMeta

    pattern = re.compile(
        r"^\[(?P<week_day>SUN|MON|TUE|WED|THU|FRI|SAT)\s(?P<month>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEPT|OCT|NOV|DEC)\s{1"
        r",2}(?P<day>\d{1,2})\s(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})\s(?P<year>\d+)\.(?P<microsecond>\d{1"
        r",3})\]\.\[(?:0x)?[0-9A-F]+\]\s$",
        re.IGNORECASE
    )

    def __init__(self, date_time):
        super(LogRecord, self).__init__()
        self.date_time = date_time


class HTTPRequest(object):
    pattern = re.compile(
        r"^(?P<method>OPTIONS|GET|HEAD|POST|PUT|DELETE|TRACE|CONNECT|PATCH)\s(?P<uri>/\S*)\sHTTP/(?P<version>\d\.\d)$",
        re.IGNORECASE
    )

    def __init__(self, method, url, version, headers, data):
        super(HTTPRequest, self).__init__()
        self.method = method
        self.url = url
        self.version = version
        self.headers = headers
        self.data = data

    @staticmethod
    def parse(match, lines):
        headers = defaultdict(list)
        for line in lines:
            if line:
                (key, value) = map(lambda s: s.strip(), line.split(":", 1))
                headers[key].append(value)
            else:
                break

        return HTTPRequest(
            method=match.group("method"),
            url=urlparse.urlparse(match.group("uri")),
            version=match.group("version"),
            headers=headers,
            data=""
        )


class HTTPResponse(object):
    pattern = re.compile(r"^HTTP/(?P<version>\d\.\d)\s(?P<status_code>\d{3})\s(?P<reason_phrase>.*)$", re.IGNORECASE)

    def __init__(self, version, status_code, reason_phrase, headers, data):
        super(HTTPResponse, self).__init__()
        self.version = version
        self.status_code = status_code
        self.reason_phrase = reason_phrase
        self.headers = headers
        self.data = data

    @staticmethod
    def parse(match, lines):
        headers = defaultdict(list)
        for line in lines:
            if line:
                (key, value) = map(lambda s: s.strip(), line.split(":", 1))
                headers[key].append(value)
            else:
                break

        return HTTPResponse(
            version=match.group("version"),
            status_code=match.group("status_code"),
            reason_phrase=match.group("reason_phrase"),
            headers=headers,
            data=""
        )


class HTTPLogRecord(LogRecord):
    def __init__(self, date_time, request, response):
        super(HTTPLogRecord, self).__init__(date_time)
        self.request = request
        self.response = response


class LogRecordParser(object):
    @staticmethod
    def parse(match, lines):
        date_time = datetime(
            year=int(match.group("year")),
            month=int(datetime.strptime(match.group("month"), "%b").month),
            day=int(match.group("day")),
            hour=int(match.group("hour")),
            minute=int(match.group("minute")),
            second=int(match.group("second")),
            microsecond=int(match.group("microsecond")) * 1000,
        )

        # Searching for HTTP request.
        request = None
        for line in lines:
            if line:
                match = re.search(HTTPRequest.pattern, line)
                if match:
                    request = HTTPRequest.parse(match, lines)
                    break
            else:
                break

        if request:
            # Searching for HTTP response.
            response = None
            for line in lines:
                if line:
                    # Crutch for skipping "Continue" response.
                    if "Expect" in request.headers and line == "HTTP/1.1 100 Continue":
                        # todo: Incorrect if there is no status line after "Continue" response.
                        line = next(lines)
                        if line == "We are completely uploaded and fine":
                            line = next(lines)
                        elif re.search(r"HTTP/\d\.\d\s\d{3}\s.+$", line):
                            line = re.split(r"(HTTP/\d\.\d\s\d{3}\s.+)", line)[1]
                        else:
                            raise NotImplementedError

                    match = re.search(HTTPResponse.pattern, line)
                    if match:
                        response = HTTPResponse.parse(match, lines)
                        break
                else:
                    # todo: Should stop on empty string, but there is issue with several empty strings before response.
                    pass
            return HTTPLogRecord(date_time=date_time, request=request, response=response)

        return LogRecord(date_time=date_time)


def iterate_log(lines):
    for line in lines:
        if line:
            match = re.search(LogRecord.pattern, line)
            if match:
                yield LogRecordParser.parse(match, lines)


def main():
    log.info("Starting bot.")

    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    while True:
        # noinspection PyBroadException
        try:
            response = bot.fetch_events()
            for event in response.json()["response"]["data"]["events"]:
                if event["type"] == "im":
                    event_data = event["eventData"]
                    source_uin = event_data["source"]["aimId"]
                    message = event_data["message"]

                    try:
                        bot.set_typing(target=source_uin, typing_status=TypingStatus.TYPING.value)

                        # Getting info for file in message.
                        (_, _, path, _, _) = urlparse.urlsplit(message)
                        file_id = path.rsplit("/", 1).pop()
                        file_info_response = bot.get_file_info(file_id=file_id)
                        if file_info_response.status_code == requests.codes.not_found:
                            raise FileNotFoundException
                        link = file_info_response.json()["file_list"].pop()["dlink"]

                        # Starting file download.
                        file_response = bot._http_session.get(link, stream=True)
                        if file_response.encoding is None:
                            file_response.encoding = 'utf-8'

                        # Downloading file and calculating stats.
                        stats = defaultdict(int)
                        status_codes = defaultdict(int)
                        for log_record in iterate_log(
                            (line for line in file_response.iter_lines(decode_unicode=True) if line is not None)
                        ):
                            if isinstance(log_record, HTTPLogRecord):
                                (request, response) = (log_record.request, log_record.response)

                                stats["requests_count"] += 1

                                if request.url.path == "/aim/startSession":
                                    stats["start_session_count"] += 1

                                if request.url.path == "/genToken":
                                    stats["gen_token_count"] += 1

                                if response:
                                    status_codes[response.status_code + " " + response.reason_phrase] += 1
                                else:
                                    stats["no_response_count"] += 1

                        bot.send_im(
                            target=source_uin,
                            message=(
                                "Total requests: {requests_count}\n    /aim/startSession: {start_session_count}\n    /g"
                                "enToken: {gen_token_count}\n\nResponse count by status code:\n{status_codes}\n\nFound "
                                "problems:\n{problems}\n\n{phrase}"
                            ).format(
                                requests_count=stats["requests_count"],
                                start_session_count=stats["start_session_count"],
                                gen_token_count=stats["gen_token_count"],
                                status_codes="\n".join([
                                    "    {code}: {count}".format(
                                        code=code, count=count
                                    ) for (code, count) in sorted(status_codes.items())
                                ]),
                                problems="    Requests without response: {no_response_count}".format(
                                    no_response_count=stats["no_response_count"]
                                ),
                                phrase=random.choice(PHRASES)
                            )
                        )
                    except FileNotFoundException:
                        bot.send_im(target=source_uin, message=random.choice(PHRASES) + " Give me your log right now!")
                    except NotImplementedError:
                        bot.send_im(target=source_uin, message=random.choice(PHRASES) + " Log format is not supported!")
                    except Exception:
                        bot.send_im(target=source_uin, message=random.choice(PHRASES) + " Something has gone wrong!")
                        raise
                    finally:
                        bot.set_typing(target=source_uin, typing_status=TypingStatus.NONE.value)
        except KeyboardInterrupt:
            log.info("Shutting down bot.")
            sys.exit()
        except Exception:
            log.exception("Exception in main loop!")


class FileNotFoundException(Exception):
    pass


if __name__ == '__main__':
    main()
