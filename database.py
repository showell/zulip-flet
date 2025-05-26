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
    display_recipient: dict[str, dict]
    stream_id: int
    topic: str
    timestamp: str
    flags: list[str]
    content: str

    @staticmethod
    def from_raw(raw_message, stream_name_to_id_dict):
        display_recipient = raw_message["display_recipient"]
        if raw_message["type"] == "stream":
            stream_id = stream_name_to_id_dict[display_recipient]
        else:
            stream_id = 0

        return Message(
            id=raw_message["id"],
            type=raw_message["type"],
            sender_id=raw_message["sender_id"],
            stream_id=stream_id,
            display_recipient=raw_message["display_recipient"],
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
        stream_name_to_id_dict = {
            s["name"]: s["stream_id"] for s in raw_streams
        }
        for message in raw_messages:
            id = message["id"]
            self.message_dict[id] = Message.from_raw(message, stream_name_to_id_dict)

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
                for recipient in message.display_recipient:
                    user_id = recipient["id"]
                    user_ids.add(user_id)

        for user_id in user_ids:
            if user_id in realm_user_dict:
                realm_user = realm_user_dict[user_id]
                self.user_dict[user_id] = User.from_raw(realm_user)
            else:
                print("\n\nUNKNOWN USER:", user_id)
                # TODO: grab system bots and mentioned users
