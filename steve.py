import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from multiprocessing.resource_tracker import register

# CREATE a one-line file called api_key.py
from api_key import API_KEY

import aiohttp

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
    realm_users: list


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

    async def process_events(self, *, register_info, callback):
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + "events"
            params = dict(
                queue_id=register_info.queue_id,
                last_event_id=register_info.last_event_id,
            )
            print("WAITING FOR EVENTS (infinite loop)")
            while True:
                print("---> start new get")
                async with session.get(url, auth=self.auth, params=params) as response:
                    assert response.status == 200
                    data = await response.json()
                    for event in data["events"]:
                        callback(event)
                        register_info.last_event_id = max(register_info.last_event_id, event["id"])
                    params["last_event_id"] = register_info.last_event_id


async def get_data(zulip_api, database):
    print("\n\n---------\n\n")
    print("FETCH MESSAGES (recent)")
    params = dict(
        anchor="newest",
        num_before=500,
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
        print(message["id"], message["content"])

        user_ids.add(message["sender_id"])

    for user_id in user_ids:
        if user_id in realm_user_dict:
            database.user_dict[user_id] = realm_user_dict[user_id]
        else:
            print("\n\nUNKNOWN USER:", user_id)

    print("\n\n---------\n\n")
    print(", ".join(sorted(user["full_name"] for user in database.user_dict.values())))


async def process_events(zulip_api, register_info):
    def handle_event(event):
        print(event)

    await zulip_api.process_events(
        register_info=register_info,
        callback=handle_event,
    )


async def main():
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    database = Database()

    register_info = await zulip_api.register()

    await get_data(zulip_api, database)
    extract_user_ids(register_info, database)
    await process_events(zulip_api, register_info)


asyncio.run(main())
