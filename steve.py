import asyncio
import json
from dataclasses import dataclass

# CREATE a one-line file called api_key.py
from api_key import API_KEY
from database import Database
from zulip import ZulipApi

# MODIFY THESE!!!
HOST = "https://chat.zulip.org"
USER_NAME = "showell30@yahoo.com"

REGISTER_OPTIONS = dict(
    include_subscribers=json.dumps(False),
    client_gravatar=json.dumps(False),
    include_streams=json.dumps(False),
    user_list_incomplete=json.dumps(True),
)


@dataclass
class RegisterInfo:
    queue_id: str
    last_event_id: int
    realm_users: list[dict]


@dataclass
class EventInfo:
    queue_id: str
    last_event_id: int


async def get_data(zulip_api, database):
    print("\n\n---------\n\n")
    print("FETCH MESSAGES (recent)")
    params = dict(
        anchor="newest",
        num_before=50,
        client_gravatar=json.dumps(False),
    )
    async with zulip_api.GET_json("messages", params) as data:
        messages = data["messages"]
        database.populate_messages(messages)


async def process_events(zulip_api, event_info):
    def handle_event(event):
        print(event)

    await zulip_api.process_events(
        event_info=event_info,
        callback=handle_event,
    )


async def populate_database(zulip_api, register_info):
    database = Database()

    await get_data(zulip_api, database)
    database.populate_users(register_info)


async def register(zulip_api):
    print("REGISTER")
    async with zulip_api.POST_json("register", REGISTER_OPTIONS) as data:
        register_info = RegisterInfo(
            queue_id=data["queue_id"],
            last_event_id=data["last_event_id"],
            realm_users=data["realm_users"],
        )
        print("queue_id:", register_info.queue_id)
        return register_info


async def main():
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    register_info = await register(zulip_api)

    await populate_database(zulip_api, register_info)

    event_info = EventInfo(
        queue_id=register_info.queue_id,
        last_event_id=register_info.last_event_id,
    )

    await process_events(zulip_api, event_info)


asyncio.run(main())
