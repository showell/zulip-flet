from pydantic import BaseModel
from topic_table import TopicTable


class Address(BaseModel):
    type: str
    topic_id: int
    user_ids: set[int]

    def name(self, *, topic_table: TopicTable) -> str:
        if self.type == "stream":
            return topic_table.get_topic(self.topic_id).name
        else:
            return ",".join(str(user_id) for user_id in self.user_ids)
