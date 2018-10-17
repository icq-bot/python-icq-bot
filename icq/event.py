from enum import Enum, unique


@unique
class EventType(Enum):
    MY_INFO = "myInfo"
    PRESENCE = "presence"
    BUDDY_LIST = "buddylist"
    TYPING = "typing"
    IM = "im"
    DATA_IM = "dataIM"
    CLIENT_ERROR = "clientError"
    SESSION_ENDED = "sessionEnded"
    OFFLINE_IM = "offlineIM"
    SENT_IM = "sentIM"
    SEND_DATA_IM = "sentDataIM"
    LIFESTREAM = "lifestream"
    USER_ADDED_TO_BUDDY_LIST = "userAddedToBuddyList"
    ALERT = "alert"
    SERVICE = "service"
    NOTIFICATION = "notification"
    MENTION_ME_MESSAGE = "mentionMeMessage"
    WEBRTC_MSG = "webrtcMsg"


class Event(object):
    def __init__(self, type_, data):
        super(Event, self).__init__()

        self.type = type_
        self.data = data

    def __repr__(self):
        return "Event(type='{self.type}', data='{self.data}')".format(self=self)
