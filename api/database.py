from pydantic import BaseModel
from message import Message
from stream import Stream
from user import User
from message_table import MessageTable
from stream_table import StreamTable
from topic_table import TopicTable
from user_table import UserTable


class Database(BaseModel):
    message_table: MessageTable
    user_table: UserTable
    stream_table: StreamTable
    topic_table: TopicTable

    @staticmethod
    def create_empty_database() -> "Database":
        return Database(
            message_table=MessageTable(),
            user_table=UserTable(),
            stream_table=StreamTable(),
            topic_table=TopicTable(),
        )

    def populate_messages(self, raw_messages: list[dict[str, object]]) -> None:
        for message in raw_messages:
            self.message_table.insert(
                Message.from_raw(message, topic_table=self.topic_table)
            )

    def populate_streams(self, raw_streams: list[dict[str, object]]) -> None:
        used_stream_ids = {
            message.get_stream_id(topic_table=self.topic_table)
            for message in self.message_table.get_rows()
            if message.address.type == "stream"
        }

        for stream in raw_streams:
            id = stream["stream_id"]
            if id in used_stream_ids:
                row = Stream.from_raw(stream)
                self.stream_table.insert(row)

    def populate_users(
        self, host: str, raw_realm_users: list[dict[str, object]]
    ) -> None:
        realm_user_dict = {user["user_id"]: user for user in raw_realm_users}

        user_ids = set()

        for message in self.message_table.get_rows():
            user_ids.add(message.sender_id)

            if message.address.type == "private":
                user_ids |= message.address.user_ids

        for user_id in user_ids:
            if user_id in realm_user_dict:
                realm_user = realm_user_dict[user_id]
                row = User.from_raw(host, realm_user)
                self.user_table.insert(row)
            else:
                print("\n\nUNKNOWN USER:", user_id)
                # TODO: grab system bots and mentioned users
