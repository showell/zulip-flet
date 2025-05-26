import asyncio
import json
from dataclasses import dataclass

# CREATE a one-line file called api_key.py
from api_key import API_KEY
from zulip import ZulipApi, EventInfo

# MODIFY THESE!!!
HOST = "https://chat.zulip.org"
USER_NAME = "showell30@yahoo.com"


@dataclass
class User:
    id: int
    name: str
    avatar_url: str


@dataclass
class Database:
    message_dict: dict
    user_dict: dict

    def __init__(self):
        self.message_dict = dict()
        self.user_dict = dict()


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
        for message in messages:
            id = message["id"]
            database.message_dict[id] = message


def extract_user_ids(register_info, database):
    realm_user_dict = {
        user["user_id"]: user
        for user in register_info.realm_users
    }

    user_ids = set()

    for id, message in database.message_dict.items():
        print(json.dumps(message, indent=2))
        user_ids.add(message["sender_id"])

        if message["type"] == "private":
            for recipient in message["display_recipient"]:
                user_id = recipient["id"]
                user_ids.add(user_id)

    for user_id in user_ids:
        if user_id in realm_user_dict:
            realm_user = realm_user_dict[user_id]
            print(realm_user)
            database.user_dict[user_id] = User(
                id=realm_user["user_id"],
                name=realm_user["full_name"],
                avatar_url=realm_user["avatar_url"]
            )
        else:
            print("\n\nUNKNOWN USER:", user_id)

    print("\n\n---------\n\n")
    print(", ".join(sorted(user.name for user in database.user_dict.values())))


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
    extract_user_ids(register_info, database)

async def main():
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    register_info = await zulip_api.register()

    await populate_database(zulip_api, register_info)

    event_info = EventInfo(
        queue_id=register_info.queue_id,
        last_event_id=register_info.last_event_id,
    )

    await process_events(zulip_api, event_info)


asyncio.run(main())
