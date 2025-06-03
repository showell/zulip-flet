from pydantic import BaseModel
from topic_table import TopicTable
from user_table import UserTable


class Address(BaseModel):
    type: str
    topic_id: int
    user_ids: set[int]

    def name(self, *, topic_table: TopicTable, user_table: UserTable) -> str:
        if self.type == "stream":
            return topic_table.get_topic(self.topic_id).name
        else:
            names = [user_table.get_row(user_id).name for user_id in self.user_ids]
            return ", ".join(sorted(names))
