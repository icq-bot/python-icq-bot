from enum import Enum


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


class Event(object):
    def __init__(self, event_type, data):
        super(Event, self).__init__()

        self.event_type = event_type
        self.data = data
