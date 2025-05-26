from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    avatar_url: str

    @staticmethod
    def from_raw(realm_user):
        return User(
            id=realm_user["user_id"],
            name=realm_user["full_name"],
            avatar_url=realm_user["avatar_url"]
        )


@dataclass
class Message:
    id: int
    type: str
    sender_id: int
    stream_id: int
    user_ids: set
    topic: str
    timestamp: str
    flags: list[str]
    content: str

    @staticmethod
    def from_raw(raw_message):
        display_recipient = raw_message["display_recipient"]
        if raw_message["type"] == "stream":
            stream_id = raw_message["stream_id"]
            user_ids = set()
        else:
            stream_id = 0
            print(display_recipient)
            user_ids = {recip["id"] for recip in display_recipient}

        return Message(
            id=raw_message["id"],
            type=raw_message["type"],
            sender_id=raw_message["sender_id"],
            stream_id=stream_id,
            user_ids=user_ids,
            topic=raw_message["subject"],
            timestamp=raw_message["timestamp"],
            flags=raw_message["flags"],
            content=raw_message["content"],
        )


@dataclass
class Database:
    message_dict: dict
    user_dict: dict

    def __init__(self):
        self.message_dict = dict()
        self.user_dict = dict()

    def populate_messages(self, raw_messages, raw_streams):
        for message in raw_messages:
            id = message["id"]
            self.message_dict[id] = Message.from_raw(message)

    def populate_users(self, raw_realm_users):
        realm_user_dict = {
            user["user_id"]: user
            for user in raw_realm_users
        }

        user_ids = set()

        for id, message in self.message_dict.items():
            print(message)
            user_ids.add(message.sender_id)

            if message.type == "private":
                user_ids |= message.user_ids

        for user_id in user_ids:
            if user_id in realm_user_dict:
                realm_user = realm_user_dict[user_id]
                self.user_dict[user_id] = User.from_raw(realm_user)
            else:
                print("\n\nUNKNOWN USER:", user_id)
                # TODO: grab system bots and mentioned users

        print(sorted(user.name for user in self.user_dict.values()))