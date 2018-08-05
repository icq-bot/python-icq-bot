import cgi
import json
import logging
import os
import re
import uuid
from signal import signal, SIGINT, SIGTERM, SIGABRT
from threading import Thread, Lock
from time import sleep

import requests
from cached_property import cached_property
from expiringdict import ExpiringDict
from monotonic import monotonic
from requests import ReadTimeout
from requests.adapters import HTTPAdapter

import icq
from icq.dispatcher import Dispatcher, StopDispatch
from icq.event import Event, EventType
from icq.filter import MessageFilter
from icq.handler import MyInfoHandler, MessageHandler
from icq.util import signal_name_by_code, invalidate_cached_property, wrap

try:
    from urllib import parse as urlparse
except ImportError:
    # noinspection PyUnresolvedReferences
    import urlparse


class ICQBot(object):
    def __init__(self, token, api_url_base=None, name=None, version=None, timeout_s=20, poll_timeout_s=60):
        super(ICQBot, self).__init__()

        self.log = logging.getLogger(__name__)

        self.token = token
        self.api_base_url = "https://botapi.icq.net" if api_url_base is None else api_url_base
        self.name = name
        self.version = version
        self.timeout_s = timeout_s
        self.poll_timeout_s = poll_timeout_s

        self.dispatcher = Dispatcher(self)
        self.dispatcher.add_handler(MyInfoHandler())
        self.running = False

        self._uin = self._nick = None
        self._fetch_base_url = None
        self._next_fetch_after_s = 0

        self.__lock = Lock()
        self.__polling_thread = None

        self.__sent_im_cache = ExpiringDict(max_len=2 ** 10, max_age_seconds=60)
        self.dispatcher.add_handler(SkipDuplicateIMHandler(self.__sent_im_cache))

    @property
    def uin(self):
        return self._uin

    @uin.setter
    def uin(self, value):
        self._uin = value
        invalidate_cached_property(self, "user_agent")

    @property
    def nick(self):
        return self._nick

    @nick.setter
    def nick(self, value):
        self._nick = value
        invalidate_cached_property(self, "user_agent")

    @cached_property
    def user_agent(self):
        return "{name}/{version} (uin={uin}; nick={nick}) python-icq-bot/{library_version}".format(
            name=self.name,
            version=self.version,
            uin="" if self.uin is None else self.uin,
            nick="" if self.nick is None else self.nick,
            library_version=icq.__version__
        )

    @cached_property
    def http_session(self):
        session = requests.Session()

        for scheme in ("http://", "https://"):
            session.mount(scheme, BotLoggingHTTPAdapter(bot=self))

        return session

    def _start_polling(self):
        while self.running:
            # Exceptions should not stop polling thread.
            # noinspection PyBroadException
            try:
                response = self.fetch_events()
                for event in response.json()["response"]["data"]["events"]:
                    self.dispatcher.dispatch(Event(type_=EventType(event["type"]), data=event["eventData"]))
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
            self.log.debug("Stopping bot by signal '{name} ({code})'. Repeat for force exit.".format(
                name=signal_name_by_code(sig), code=sig
            ))
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
        poll_timeout_s = self.poll_timeout_s if poll_timeout_s is None else poll_timeout_s

        if self._fetch_base_url:
            (scheme, netloc, path, query, _) = urlparse.urlsplit(self._fetch_base_url)
            url = "{scheme}://{netloc}{path}".format(scheme=scheme, netloc=netloc, path=path)
            params = urlparse.parse_qs(query, keep_blank_values=True)
        else:
            url = "{}/fetchEvents".format(self.api_base_url)
            params = {"first": [1]}

        params.update({
            "r": uuid.uuid4(),
            "aimsid": [self.token],
            "timeout": [int(poll_timeout_s) * 1000]
        })

        time_to_wait_s = self._next_fetch_after_s - monotonic()
        if time_to_wait_s > 0:
            self.log.debug("Sleeping for {:.3f} seconds before next fetch.".format(time_to_wait_s))
            sleep(time_to_wait_s)

        try:
            result = self.http_session.get(url=url, params=params, timeout=poll_timeout_s + self.timeout_s)
            result_data = result.json()["response"]["data"]
            self._next_fetch_after_s = monotonic() + result_data.get("timeToNextFetch", 1) / 1000
            self._fetch_base_url = result_data["fetchBaseURL"]
        except Exception:
            self._next_fetch_after_s = monotonic() + 1
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

    def chat_add(self, chat_id, members):
        return self.http_session.post(
            url="{}/chat/add".format(self.api_base_url),
            data={
                "r": uuid.uuid4(),
                "aimsid": self.token,
                "chat_id": chat_id,
                "members": members if isinstance(members, six.string_types) else ";".join(members)
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

    def sticker_pack_info(self, store_id=None, pack_id=None, file_id=None):
        if store_id is None and pack_id is None and file_id is None:
            raise ValueError("Either 'store_id' or 'pack_id' or 'file_id' must be specified!")

        return self.http_session.get(
            url="{}/store/packinfo".format(self.api_base_url),
            params={
                "store_id": store_id,
                "id": pack_id,
                "file_id": file_id
            },
            timeout=self.timeout_s
        )

    def download_sticker(self, sticker_id, sticker_size):
        # noinspection PyProtectedMember
        match = MessageFilter._StickerFilter.STICKER_ID_REGEXP.search(string=sticker_id)
        if match:
            ext = match.group("ext")
            sticker = match.group("sticker")
            pack_info_response_json = self.sticker_pack_info(pack_id=ext).json()

            return self.http_session.get(
                url="{base_url}/{base_url_postfix}/{ext}/{sticker}/{size}".format(
                    base_url=pack_info_response_json["base_url"],
                    base_url_postfix=pack_info_response_json["base_url_postfix"],
                    ext=ext,
                    sticker=sticker,
                    size=sticker_size.value
                ),
                timeout=self.timeout_s,
                stream=True
            )

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

    def get_history(self, sn, from_msg_id, count, patch_version="init", till_msg_id=None):
        params = {
            "sn": sn,
            "fromMsgId": from_msg_id,
            "count": count,
            "patchVersion": patch_version
        }

        if till_msg_id is not None:
            params.update({"tillMsgId": till_msg_id})

        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "getHistory",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": params
            },
            timeout=self.timeout_s
        )

    def mod_chat_member(self, stamp, member_sn, role):
        return self.http_session.post(
            url="{}/rapi".format(self.api_base_url),
            json={
                "method": "modChatMember",
                "reqId": str(uuid.uuid4()),
                "aimsid": self.token,
                "params": {
                    "stamp": stamp,
                    "memberSn": member_sn,
                    "role": role
                }
            },
            timeout=self.timeout_s
        )

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

    def send_im(self, target, message, mentions=None, parse=None, wrap_length=5000):
        """
        Send text message.

        :param target: Target user UIN or chat ID.
        :param message: Message text.
        :param mentions: Iterable with UINs to mention in message.
        :param parse: Iterable with several values from :class:`icq.constant.MessageParseType` specifying which message
            items should be parsed by target client (making preview, snippets, etc.). Specify empty iterable to avoid
            parsing message at target client. By default all types are included.
        :param wrap_length: Maximum length of symbols in one message. Text exceeding this length will be sent in several
            messages.

        :return: HTTP response.
        """
        try:
            for text in wrap(string=message, length=wrap_length):
                response = self.http_session.post(
                    url="{}/im/sendIM".format(self.api_base_url),
                    data={
                        "r": uuid.uuid4(),
                        "aimsid": self.token,
                        "t": target,
                        "message": text,
                        "mentions": ",".join(mentions) if mentions is not None else None,
                        "parse": json.dumps([p.value for p in parse]) if parse is not None else None
                    },
                    timeout=self.timeout_s
                )

                self.__sent_im_cache[response.json()["response"]["data"]["msgId"]] = text
        except ReadTimeout:
            self.log.exception("Timeout while sending request!")

    def send_sticker(self, target, sticker_id):
        try:
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
        except ReadTimeout:
            self.log.exception("Timeout while sending request!")

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
        return "\n".join((u"{key}: {value}".format(key=key, value=value) for (key, value) in headers.items()))

    @staticmethod
    def _body_to_string(body):
        return body.decode("utf-8") if isinstance(body, bytes) else body

    def __init__(self, *args, **kwargs):
        super(LoggingHTTPAdapter, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug(u"{method} {url}\n{headers}{body}".format(
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
            self.log.debug(u"{status_code} {reason}\n{headers}{body}".format(
                status_code=response.status_code,
                reason=response.reason,
                headers=LoggingHTTPAdapter._headers_to_string(response.headers),
                body="\n\n" + (
                    response.text if LoggingHTTPAdapter._is_loggable(response.headers) else "[binary data]"
                ) if response.content is not None else ""
            ))

        return response


class BotLoggingHTTPAdapter(LoggingHTTPAdapter):
    def __init__(self, bot, *args, **kwargs):
        super(BotLoggingHTTPAdapter, self).__init__(*args, **kwargs)

        self.bot = bot

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        request.headers["User-Agent"] = self.bot.user_agent
        return super(BotLoggingHTTPAdapter, self).send(request, stream, timeout, verify, cert, proxies)


class FileNotFoundException(Exception):
    pass


class SkipDuplicateIMHandler(MessageHandler):
    def __init__(self, cache):
        super(SkipDuplicateIMHandler, self).__init__(filters=MessageFilter.message)

        self.cache = cache

    def check(self, event, dispatcher):
        if super(SkipDuplicateIMHandler, self).check(event=event, dispatcher=dispatcher):
            if self.cache.get(event.data["msgId"]) == event.data["message"]:
                raise StopDispatch
