import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

import aiohttp

# CREATE a one-line file called api_key.py
from api_key import API_KEY

# MODIFY THESE!!!
HOST = "https://chat.zulip.org"
USER_NAME = "showell30@yahoo.com"

SLIM_CONFIG = dict(
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


class ZulipApi:
    def __init__(self, host, user_name, api_key):
        self.auth = aiohttp.BasicAuth(user_name, api_key)
        self.url_prefix = host + "/api/v1/"

    @asynccontextmanager
    async def post(self, url_ending, data):
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + url_ending
            async with session.post(url, auth=self.auth, data=data) as response:
                yield response

    @asynccontextmanager
    async def POST_json(self, url_ending, data):
        async with self.post(url_ending, data) as response:
            assert response.status == 200
            yield await response.json()

    @asynccontextmanager
    async def get(self, url_ending, params):
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + url_ending
            async with session.get(url, auth=self.auth, params=params) as response:
                yield response

    @asynccontextmanager
    async def GET_json(self, url_ending, params):
        async with self.get(url_ending, params) as response:
            assert response.status == 200
            data = await response.json()
            assert data["result"] == "success"
            yield data

    async def register(self):
        print("REGISTER")
        async with self.POST_json("register", SLIM_CONFIG) as data:
            register_info = RegisterInfo(
                queue_id=data["queue_id"],
                last_event_id=data["last_event_id"],
                realm_users=data["realm_users"],
            )
            print("queue_id:", register_info.queue_id)
            return register_info

    async def process_events(self, *, event_info, callback):
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + "events"
            print("WAITING FOR EVENTS (infinite loop)")
            while True:
                print("---> start new get")
                async with session.get(url, auth=self.auth, params=asdict(event_info)) as response:
                    assert response.status == 200
                    data = await response.json()
                    for event in data["events"]:
                        callback(event)
                        event_info.last_event_id = max(event_info.last_event_id, event["id"])


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


async def main():
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    database = Database()

    register_info = await zulip_api.register()

    await get_data(zulip_api, database)
    extract_user_ids(register_info, database)

    event_info = EventInfo(
        queue_id=register_info.queue_id,
        last_event_id=register_info.last_event_id,
    )
    await process_events(zulip_api, event_info)


asyncio.run(main())
