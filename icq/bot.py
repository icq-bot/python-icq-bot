import cgi
import logging
import os
import re
import uuid
from signal import signal, SIGINT, SIGTERM, SIGABRT
from threading import Thread, Lock
from time import time, sleep

import requests
from cached_property import cached_property
from requests.adapters import HTTPAdapter

from icq.dispatcher import Dispatcher
from icq.event import Event, EventType
from icq.filter import MessageFilter

try:
    from urllib import parse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse as parse


class ICQBot(object):
    def __init__(self, token, api_url_base=None, name=None, version=None, timeout_s=5.0, poll_timeout_s=60.0):
        super(ICQBot, self).__init__()

        self.log = logging.getLogger(__name__)

        self.token = token
        self.api_base_url = "https://botapi.icq.net" if api_url_base is None else api_url_base
        self.name = name
        self.version = version
        self.timeout_s = timeout_s
        self.poll_timeout_s = poll_timeout_s

        self.user = None
        self.dispatcher = Dispatcher(self)
        self.running = False

        self._fetch_base_url = None
        self._next_fetch_after_s = 0

        self.__lock = Lock()
        self.__polling_thread = None

    @cached_property
    def _user_agent(self):
        return "{name}/{version} (uin={uin}; nick={nick}) python-icq-bot/0.0.7".format(
            name=self.name, version=self.version, uin="", nick=""
        )

    @cached_property
    def http_session(self):
        session = requests.Session()

        for scheme in ("http://", "https://"):
            session.mount(scheme, LoggingHTTPAdapter())

        session.headers["User-Agent"] = self._user_agent

        return session

    def _start_polling(self):
        while self.running:
            # Exceptions should not stop polling thread.
            # noinspection PyBroadException
            try:
                response = self.fetch_events()
                for event in response.json()["response"]["data"]["events"]:
                    self.dispatcher.dispatch(Event(event_type=EventType(event["type"]), data=event["eventData"]))
            except Exception:
                self.log.exception("Exception while polling!")

    def start_polling(self):
        with self.__lock:
            if not self.running:
                self.log.info("Starting polling.")

                self.running = True

                self.__polling_thread = Thread(target=self._start_polling)
                self.__polling_thread.start()

    def _start_webhook_service(self):
        pass

    def start_webhook_service(self):
        with self.__lock:
            if not self.running:
                self.log.info("Starting webhook service.")

                self.running = True

    def stop(self):
        with self.__lock:
            if self.running:
                self.log.info("Stopping bot.")

                self.running = False

                self.__polling_thread.join()

    # noinspection PyUnusedLocal
    def _signal_handler(self, sig, stack_frame):
        if self.running:
            self.stop()
        else:
            self.log.warning("Force exiting.")
            # It's fine here, this is standard way to force exit.
            # noinspection PyProtectedMember
            os._exit(1)

    def idle(self):
        for sig in (SIGINT, SIGTERM, SIGABRT):
            signal(sig, self._signal_handler)

        while self.running:
            sleep(1)

    def fetch_events(self, poll_timeout_s=None):
        poll_timeout_s = (self.poll_timeout_s if poll_timeout_s is None else poll_timeout_s) * 1000

        if self._fetch_base_url:
            (scheme, netloc, path, query, _) = parse.urlsplit(self._fetch_base_url)
            url = "{scheme}://{netloc}{path}".format(scheme=scheme, netloc=netloc, path=path)
            params = parse.parse_qs(query, keep_blank_values=True)
        else:
            url = "{}/fetchEvents".format(self.api_base_url)
            params = {"first": [1]}

        params.update({
            "r": uuid.uuid4(),
            "aimsid": [self.token],
            "timeout": [int(poll_timeout_s)]
        })

        time_to_wait_s = self._next_fetch_after_s - time()
        if time_to_wait_s > 0:
            self.log.debug("Sleeping for {:.3f} seconds before next fetch.".format(time_to_wait_s))
            sleep(time_to_wait_s)

        try:
            result = self.http_session.get(url=url, params=params, timeout=poll_timeout_s + self.timeout_s)
            result_data = result.json()["response"]["data"]
            self._next_fetch_after_s = time() + result_data.get("timeToNextFetch", 1) / 1000
            self._fetch_base_url = result_data["fetchBaseURL"]
        except Exception:
            self._next_fetch_after_s = time() + 1
            raise

        return result

    def block_chat_members(self, sn, members):
        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "blockChatMembers",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": {"sn": sn, "members": members}
            },
            timeout=self.timeout_s
        )

    def chat_resolve_pending(self, sn, members):
        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "chatResolvePending",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": {"sn": sn, "members": members}
            },
            timeout=self.timeout_s
        )

    def del_message(self, sn, msg_id, shared=None):
        params = {"sn": sn, "msgId": msg_id}
        if shared is not None:
            params.update({"shared": shared})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "delMsg",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def download_file(self, url):
        # noinspection PyProtectedMember
        match = MessageFilter._FileFilter.FILE_URL_REGEXP.search(url)
        if match:
            info_response = self.get_file_info(file_id=match.group("file_id"))

            file_list = info_response.json()["file_list"]
            result = (self.http_session.get(url=f["dlink"], timeout=self.timeout_s, stream=True) for f in file_list)

            return next(result) if len(file_list) == 1 else result

    def get_buddy_list(self):
        return self.http_session.get(
            url="{}/getBuddyList".format(self.api_base_url),
            params={
                "r": uuid.uuid4(),
                "aimsid": self.token
            },
            timeout=self.timeout_s
        )

    def get_chat_admins(self, stamp=None, sn=None, member_limit=None):
        params = {}
        if stamp is not None:
            params.update({"stamp": stamp})
        if sn is not None:
            params.update({"sn": sn})
        if member_limit is not None:
            params.update({"memberLimit": member_limit})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "getChatAdmins",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def get_chat_blocked(self, sn, member_limit=None):
        params = {"sn": sn}
        if member_limit is not None:
            params.update({"memberLimit": member_limit})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "getChatBlocked",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def get_chat_info(self, stamp=None, sn=None, member_limit=None):
        params = {}
        if stamp is not None:
            params.update({"stamp": stamp})
        if sn is not None:
            params.update({"sn": sn})
        if member_limit is not None:
            params.update({"memberLimit": member_limit})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "getChatInfo",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def get_chat_pending(self, sn, member_limit=None):
        params = {"sn": sn}
        if member_limit is not None:
            params.update({"memberLimit": member_limit})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "getPendingList",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def get_file_info(self, file_id):
        response = self.http_session.get(
            url="{}/files/getInfo".format(self.api_base_url),
            params={"file_id": file_id},
            timeout=self.timeout_s
        )
        if response.status_code == requests.codes.not_found:
            raise FileNotFoundException

        return response

    def pin_message(self, sn, msg_id, unpin=None):
        params = {"sn": sn, "msgId": msg_id}
        if unpin is not None:
            params.update({"unpin": unpin})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "pinMessage",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def remove_buddy(self, buddy, group=None, all_groups=True):
        return self.http_session.post(
            url="{}/buddylist/removeBuddy".format(self.api_base_url),
            data={
                "r": uuid.uuid4(),
                "aimsid": self.token,
                "buddy": buddy,
                "group": group,
                "allGroups": "1" if all_groups else "0"
            },
            timeout=self.timeout_s
        )

    def send_file(self, file, name=None):
        return self.http_session.post(
            url="{}/im/sendFile".format(self.api_base_url),
            params={
                "aimsid": self.token,
                "filename": name
            },
            data=file,
            stream=True,
            timeout=self.timeout_s
        )

    def send_im(self, target, message):
        return self.http_session.post(
            url="{}/im/sendIM".format(self.api_base_url),
            data={
                "r": uuid.uuid4(),
                "aimsid": self.token,
                "t": target,
                "message": message
            },
            timeout=self.timeout_s
        )

    def send_sticker(self, target, sticker_id):
        return self.http_session.post(
            url="{}/im/sendSticker".format(self.api_base_url),
            data={
                "r": uuid.uuid4(),
                "aimsid": self.token,
                "t": target,
                "stickerId": sticker_id
            },
            timeout=self.timeout_s
        )

    def set_typing(self, target, typing_status):
        return self.http_session.post(
            url="{}/im/setTyping".format(self.api_base_url),
            data={
                "r": uuid.uuid4(),
                "aimsid": self.token,
                "t": target,
                "typingStatus": typing_status.value
            },
            timeout=self.timeout_s
        )

    def unblock_chat_members(self, sn, members):
        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "unblockChatMembers",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": {"sn": sn, "members": members}
            },
            timeout=self.timeout_s
        )

    def validate_sid(self):
        return self.http_session.get(
            url="{}/aim/validateSid".format(self.api_base_url),
            params={
                "r": uuid.uuid4(),
                "aimsid": self.token
            },
            timeout=self.timeout_s
        )


class LoggingHTTPAdapter(HTTPAdapter):
    _LOG_MIME_TYPE_REGEXP = re.compile(
        r"^(?:text(?:/.+)?|application/(?:json|javascript|xml|x-www-form-urlencoded))$", re.IGNORECASE
    )

    @staticmethod
    def _is_loggable(headers):
        return LoggingHTTPAdapter._LOG_MIME_TYPE_REGEXP.search(cgi.parse_header(headers.get("Content-Type", ""))[0])

    @staticmethod
    def _headers_to_string(headers):
        return "\n".join(("{key}: {value}".format(key=key, value=value) for (key, value) in headers.items()))

    @staticmethod
    def _body_to_string(body):
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def __init__(self, *args, **kwargs):
        super(LoggingHTTPAdapter, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("{method} {url}\n{headers}{body}\n".format(
                method=request.method,
                url=request.url,
                headers=LoggingHTTPAdapter._headers_to_string(request.headers),
                body="\n\n" + (
                    LoggingHTTPAdapter._body_to_string(request.body) if
                    LoggingHTTPAdapter._is_loggable(request.headers) else "[binary data]"
                ) if request.body is not None else ""
            ))

        response = super(LoggingHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)

        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("{status_code} {reason}\n{headers}{body}\n".format(
                status_code=response.status_code,
                reason=response.reason,
                headers=LoggingHTTPAdapter._headers_to_string(response.headers),
                body="\n\n" + (
                    response.text if LoggingHTTPAdapter._is_loggable(response.headers) else "[binary data]"
                ) if response.content is not None else ""
            ))

        return response


class FileNotFoundException(Exception):
    pass
