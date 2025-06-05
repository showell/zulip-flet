from dataclasses import dataclass
import json
from typing import Any
from zulip import ZulipApi

REGISTER_OPTIONS = dict(
    apply_markdown=json.dumps(False),
    include_subscribers=json.dumps(False),
    client_gravatar=json.dumps(False),
    include_streams=json.dumps(False),
    user_list_incomplete=json.dumps(True),
)


@dataclass
class RegisterInfo:
    queue_id: str
    last_event_id: int
    realm_users: list[dict[str, Any]]
    streams: list[dict[str, Any]]


async def register(zulip_api: ZulipApi) -> RegisterInfo:
    print("REGISTER")
    async with zulip_api.POST_json("register", REGISTER_OPTIONS) as data:
        register_info = RegisterInfo(
            queue_id=data["queue_id"],
            last_event_id=data["last_event_id"],
            realm_users=data["realm_users"] + data["cross_realm_bots"],
            streams=data["streams"],
        )
        print("queue_id:", register_info.queue_id)
        return register_info
