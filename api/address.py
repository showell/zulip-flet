from pydantic import BaseModel
from stream_table import StreamTable
from topic_table import TopicTable
from user_table import UserTable


class Address(BaseModel):
    type: str
    topic_id: int
    user_ids: set[int]

    def name(
        self,
        *,
        stream_table: StreamTable,
        topic_table: TopicTable,
        user_table: UserTable,
    ) -> str:
        if self.type == "stream":
            topic = topic_table.get_topic(self.topic_id)
            stream = stream_table.get_row(topic.stream_id)
            return f"{stream.name}: {topic.name}"
        else:
            names = [user_table.get_row(user_id).name for user_id in self.user_ids]
            return ", ".join(sorted(names))
