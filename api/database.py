from pydantic import BaseModel
from user import User
from stream import Stream
from message_table import MessageTable


class Database(BaseModel):
    message_table: MessageTable
    user_dict: dict[int, User]
    stream_dict: dict[int, Stream]

    @staticmethod
    def create_empty_database():
        return Database(
            message_table=MessageTable(),
            user_dict={},
            stream_dict={},
        )

    def populate_messages(self, raw_messages):
        self.message_table.insert_many(raw_messages)

    def populate_streams(self, raw_streams):
        used_stream_ids = {
            message.stream_id for message in self.message_table.get_rows()
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

        for message in self.message_table.get_rows():
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
