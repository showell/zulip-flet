from pydantic import BaseModel


class Address(BaseModel):
    type: str
    topic_id: int
