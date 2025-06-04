from pydantic import BaseModel


class MessageListConfig(BaseModel):
    label: str
