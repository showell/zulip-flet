from pydantic import BaseModel

class Topic(BaseModel):
    stream_id: int
    name: str

    def key(self) -> str:
        return f"{self.stream_id},{self.name}"

class TopicTable(BaseModel):
    id_seq: int = 0
    get_id_dict: dict[str, int] = {}

    def get_topic_id(self, stream_id: int, topic_str: str) -> int:
        topic_key = Topic(stream_id=stream_id, name=topic_str).key()
        if topic_key in self.get_id_dict.keys():
            return self.get_id_dict[topic_key]
        self.id_seq += 1
        self.get_id_dict[topic_key] = self.id_seq
        return self.id_seq