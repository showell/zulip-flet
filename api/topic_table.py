from pydantic import BaseModel
from topic import Topic


class TopicTable(BaseModel):
    id_seq: int = 0
    get_id_dict: dict[str, int] = {}
    topic_dict: dict[int, Topic] = {}

    def get_topic_id(self, stream_id: int, topic_str: str) -> int:
        topic = Topic(stream_id=stream_id, name=topic_str)
        topic_key = topic.key()
        if topic_key in self.get_id_dict.keys():
            return self.get_id_dict[topic_key]
        self.id_seq += 1
        topic_id = self.id_seq
        self.get_id_dict[topic_key] = topic_id
        self.topic_dict[topic_id] = topic
        return self.id_seq

    def get_topic(self, topic_id: int) -> Topic:
        return self.topic_dict[topic_id]

    def get_sorted_rows(self, *, stream_table):
        topics = self.topic_dict.values()
        return sorted(topics, key=lambda topic: topic.label(stream_table=stream_table))
