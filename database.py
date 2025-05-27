from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    avatar_url: str

    @staticmethod
    def from_raw(host, realm_user):
        avatar_url = realm_user["avatar_url"]
        if avatar_url.startswith("/"):
            avatar_url = host + avatar_url
        return User(
            id=realm_user["user_id"],
            name=realm_user["full_name"],
            avatar_url=avatar_url,
        )


class Stream(BaseModel):
    id: int
    name: str

    @staticmethod
    def from_raw(raw_stream):
        return Stream(
            id=raw_stream["stream_id"],
            name=raw_stream["name"],
        )


class Message(BaseModel):
    id: int
    type: str
    sender_id: int
    stream_id: int
    user_ids: set
    topic: str
    timestamp: int
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


class Database(BaseModel):
    message_dict: dict[int, Message]
    user_dict: dict[int, User]
    stream_dict: dict[int, Stream]

    @staticmethod
    def create_empty_database():
        return Database(
            message_dict={},
            user_dict={},
            stream_dict={},
        )

    async def get_user(self, user_id):
        if user_id == 5:
            user_id = 58 # HUGE HACK
        return self.user_dict[user_id]

    def populate_messages(self, raw_messages):
        for message in raw_messages:
            id = message["id"]
            self.message_dict[id] = Message.from_raw(message)

    def populate_streams(self, raw_streams):
        assert (len(self.message_dict) >= 10)  # sanity check
        used_stream_ids = {
            message.stream_id for message in self.message_dict.values()
        }

        for stream in raw_streams:
            id = stream["stream_id"]
            if id in used_stream_ids:
                self.stream_dict[id] = Stream.from_raw(stream)

        print(self.stream_dict)

    def populate_users(self, host, raw_realm_users):
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
                self.user_dict[user_id] = User.from_raw(host, realm_user)
            else:
                print("\n\nUNKNOWN USER:", user_id)
                # TODO: grab system bots and mentioned users

        print(sorted(user.name for user in self.user_dict.values()))
