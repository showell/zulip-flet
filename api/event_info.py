from dataclasses import dataclass


@dataclass
class EventInfo:
    queue_id: str
    last_event_id: int
