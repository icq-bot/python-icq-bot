import logging.config
import random
import re
from collections import defaultdict
from datetime import datetime
from enum import Enum

import requests

from example.util import log_call
from icq.bot import ICQBot, FileNotFoundException
from icq.constant import TypingStatus
from icq.filter import MessageFilter
from icq.handler import MessageHandler

try:
    from urllib import parse
except ImportError:
    import urlparse as parse

logging.config.fileConfig("logging.ini")
log = logging.getLogger(__name__)

NAME = "Hermes Bot"
VERSION = "0.0.2"
TOKEN = "000.0000000000.0000000000:000000000"

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


def logging_iterator(name, iterable):
    for item in iterable:
        log.debug("Processing line ({name}): '{item}'.".format(name=name, item=item))
        yield item


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    PUT = "PUT"
    DELETE = "DELETE"
    TRACE = "TRACE"
    CONNECT = "CONNECT"
    PATCH = "PATCH"


class HTTPRequest(object):
    pattern = re.compile(r"^Connected to (?P<host>\S+) \((?P<ip>[^)]+)\) port (?P<port>\d+) \(#\d+\)$", re.IGNORECASE)

    _pattern_request_line = re.compile(
        r"^(?P<method>" + "|".join(m.value for m in HTTPMethod) + r")\s(?P<uri>/\S*)\sHTTP/(?P<version>\d\.\d)$",
        flags=re.IGNORECASE
    )

    _pattern_http_header = re.compile(
        r"^\s*(?P<name>X-[^:]*?|Host|User-Agent|Accept|Accept-Encoding|Connection|Content-Length|Content-Type|Expect|If"
        r"-None-Match)\s*:\s*(?P<value>.*?)\s*$", flags=re.IGNORECASE
    )

    @log_call
    def __init__(self, ip, method, url, version, headers, data):
        super(HTTPRequest, self).__init__()

        self.ip = ip
        self.method = method
        self.url = url
        self.version = version
        self.headers = headers
        self.data = data

    @staticmethod
    @log_call
    def parse(match, lines):
        for line in lines:
            request_line_match = HTTPRequest._pattern_request_line.search(line)
            if request_line_match:
                log.debug("Line matched with 'HTTPRequest._pattern_request_line' pattern.")
                break
        else:
            raise ParseException("Can't find request line!")

        headers = defaultdict(list)
        for line in lines:
            header_match = re.search(HTTPRequest._pattern_http_header, line)
            if header_match:
                headers[header_match.group("name")].append(header_match.group("value"))
            else:
                break

        method = HTTPMethod(request_line_match.group("method"))

        # Crutch for handling "Expect" request.
        if "Expect" in headers:
            if len(headers["Expect"]) != 1 and headers["Expect"][0] != "100-continue":
                raise ParseException("Unknown 'Expect' request header value ('{}')!".format(headers["Expect"]))

            line = next(lines)
            if line != "HTTP/1.1 100 Continue":
                raise ParseException("Unknown status line ('{}') for 'Expect' response!".format(line))

            line = next(lines)
            if line == "We are completely uploaded and fine":
                # No data, seems like client logging bug.
                data = None
            else:
                data = line
        else:
            if method is HTTPMethod.GET:
                data = None
            elif method is HTTPMethod.POST:
                data = next(lines)
            else:
                raise ParseException("Unsupported HTTP method ('{}')!".format(method))

        return HTTPRequest(
            ip=match.group("ip"),
            method=method,
            url=parse.urlparse("{scheme}://{host}{uri}".format(
                scheme={80: "HTTP", 443: "HTTPS"}[int(match.group("port"))],
                host=match.group("host"),
                uri=request_line_match.group("uri")
            )),
            version=request_line_match.group("version"),
            headers=headers,
            data=data
        )

    def __repr__(self):
        return (
            "HTTPRequest(method='{self.method}', url='{self.url}', version='{self.version}', headers='{self.headers}', "
            "data='{self.data}')".format(self=self)
        )


class HTTPResponse(object):
    pattern = re.compile(r"^HTTP/(?P<version>\d\.\d)\s(?P<status_code>\d{3})\s(?P<reason_phrase>.+)$", re.IGNORECASE)

    _pattern_http_header = re.compile(
        r"^\s*(?P<name>X-[^:]*?|Server|Date|Content-Type|Content-Length|Content-Encoding|Connection|Keep-Alive|Access-C"
        r"ontrol-Allow-Origin|Transfer-Encoding|Pragma|Cache-Control|ETag|Strict-Transport-Security|Set-Cookie)\s*:\s*("
        r"?P<value>.*?)\s*$", re.IGNORECASE
    )

    _pattern_elapsed = re.compile(r"^Completed in (?P<elapsed>\d+) ms$", re.IGNORECASE)

    @log_call
    def __init__(self, version, status_code, reason_phrase, headers, data, elapsed):
        super(HTTPResponse, self).__init__()

        self.version = version
        self.status_code = status_code
        self.reason_phrase = reason_phrase
        self.headers = headers
        self.data = data
        self.elapsed = elapsed

    @staticmethod
    @log_call
    def parse(match, lines):
        headers = defaultdict(list)
        for line in lines:
            (key, value) = map(lambda s: s.strip(), line.split(":", 1))
            headers[key].append(value)

        data = next(lines)

        for line in lines:
            elapsed_match = re.search(HTTPResponse._pattern_elapsed, line)
            if elapsed_match:
                log.debug("Line matched with 'HTTPResponse._pattern_elapsed' pattern.")
                elapsed = elapsed_match.group("elapsed")
                break
        else:
            raise ParseException("Can't find elapsed time!")

        return HTTPResponse(
            version=match.group("version"),
            status_code=match.group("status_code"),
            reason_phrase=match.group("reason_phrase"),
            headers=headers,
            data=data,
            elapsed=elapsed
        )

    def __repr__(self):
        return (
            "HTTPResponse(version='{self.version}', status_code='{self.status_code}', reason_phrase='{self.reason_phras"
            "e}', headers='{self.headers}', data='{self.data}', elapsed='{self.elapsed}')".format(self=self)
        )


class LogRecord(object):
    pattern = re.compile(
        r"^\[(?P<week_day>Sun|Mon|Tue|Wed|Thu|Fri|Sat)\s(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s{1,"
        r"2}(?P<day>\d{1,2})\s(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})\s(?P<year>\d+)\.(?P<microsecond>\d{1,"
        r"3})\]\.\[(?:0x)?[0-9a-fA-F]+\]\s*$", re.IGNORECASE
    )

    @log_call
    def __init__(self, date_time, request=None, response=None):
        super(LogRecord, self).__init__()

        self.date_time = date_time
        self.request = request
        self.response = response

    @staticmethod
    @log_call
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

        for line in lines:
            request_match = HTTPRequest.pattern.search(line)
            if request_match:
                log.debug("Line matched with 'HTTPRequest.pattern' pattern.")

                buffer = []
                # noinspection PyAssignmentToLoopOrWithParameter
                for line in lines:
                    response_match = re.search(HTTPResponse.pattern, line)
                    if response_match:
                        log.debug("Line matched with 'HTTPResponse.pattern' pattern.")
                        return LogRecord(
                            date_time=date_time,
                            request=HTTPRequest.parse(request_match, logging_iterator(HTTPRequest.__name__, buffer)),
                            response=HTTPResponse.parse(
                                response_match, logging_iterator(HTTPResponse.__name__, list(lines))
                            )
                        )
                    else:
                        buffer.append(line)

        return LogRecord(date_time=date_time)


def fix_log(lines):
    status_line_regexp = re.compile(r"^(?P<body>.*)(?P<status_line>HTTP/\d\.\d\s\d{3}\s.+)$", re.IGNORECASE)
    connection_left_regexp = re.compile(r"^.*Connection #\d+ to host \S+ left intact$", re.IGNORECASE)
    upload_sent_regexp = re.compile(r"^.*upload completely sent off: \d+ out of \d+ bytes$", re.IGNORECASE)

    prev_line = None
    for line in lines:
        log.debug("Processing line: '{}'.".format(line))

        if prev_line == "HTTP/1.1 100 Continue":
            match = re.search(status_line_regexp, line)
            if match:
                log.debug("Fixing '100-continue' problem line.")
                yield match.group("body")
                yield match.group("status_line")
        elif re.search(connection_left_regexp, line):
            log.debug("Fixing 'Connection blah-blah left intact' problem line.")
            # yield re.split(connection_left_split_regexp, line)[0]
        elif re.search(upload_sent_regexp, line):
            log.debug("Fixing 'Upload completely sent blah-blah' problem line.")
            # result = re.split(upload_sent_split_regexp, line)[0]
        else:
            yield line

        prev_line = line


def iterate_log(lines):
    buffer = []
    match = None
    for line in lines:
        m = re.search(LogRecord.pattern, line)
        if m:
            log.debug("Line matched with 'LogRecord.pattern' pattern.")

            if buffer and match:
                yield LogRecord.parse(match, logging_iterator(LogRecord.__name__, buffer))

            buffer = []
            match = m
        else:
            buffer.append(line)


def file_callback(bot, event):
    source_uin = event.data["source"]["aimId"]
    message = event.data["message"]

    try:
        bot.set_typing(target=source_uin, typing_status=TypingStatus.TYPING)

        # Getting info for file in message.
        path = parse.urlsplit(message.strip()).path
        file_id = path.rsplit("/", 1).pop()
        file_info_response = bot.get_file_info(file_id=file_id)
        if file_info_response.status_code == requests.codes.not_found:
            raise FileNotFoundException
        url = file_info_response.json()["file_list"].pop()["dlink"]

        # Starting file download.
        file_response = bot.http_session.get(url, stream=True)
        if file_response.encoding is None:
            file_response.encoding = "utf-8"

        # Downloading file and calculating stats.
        stats = defaultdict(int)
        status_codes = defaultdict(int)
        for log_record in iterate_log(fix_log(
            line for line in file_response.iter_lines(chunk_size=1024, decode_unicode=True) if line
        )):
            if log_record.request:
                stats["requests_count"] += 1

                if log_record.request.url.path == "/aim/startSession":
                    stats["start_session_count"] += 1

                if log_record.request.url.path == "/genToken":
                    stats["gen_token_count"] += 1

                if log_record.response:
                    key = log_record.response.status_code + " " + log_record.response.reason_phrase
                    status_codes[key] += 1
                else:
                    stats["no_response_count"] += 1

        bot.send_im(
            target=source_uin,
            message=(
                "Total requests: {requests_count}\n    /aim/startSession: {start_session_count}\n    /genToken: {gen_to"
                "ken_count}\n\nResponse count by status code:\n{status_codes}\n\nFound problems:\n{problems}\n\n{phrase"
                "}"
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
    except ParseException as e:
        bot.send_im(
            target=source_uin,
            message="{phrase} Log format is not supported! Error: '{error}'.".format(
                phrase=random.choice(PHRASES), error=e
            )
        )
        raise
    except Exception:
        bot.send_im(target=source_uin, message=random.choice(PHRASES) + " Something has gone wrong!")
        raise
    finally:
        bot.set_typing(target=source_uin, typing_status=TypingStatus.NONE)


class ParseException(Exception):
    pass


def main():
    # Creating a new bot instance.
    bot = ICQBot(token=TOKEN, name=NAME, version=VERSION)

    # Registering message handlers.
    bot.dispatcher.add_handler(MessageHandler(
        callback=file_callback,
        filters=MessageFilter.file & ~(MessageFilter.image | MessageFilter.video | MessageFilter.audio)
    ))

    # Starting a polling thread watching for new events from server. This is a non-blocking call.
    bot.start_polling()

    # Blocking the current thread while the bot is working until SIGINT, SIGTERM or SIGABRT is received.
    bot.idle()


if __name__ == "__main__":
    main()
