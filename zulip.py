import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict

import aiohttp


@dataclass
class RegisterInfo:
    queue_id: str
    last_event_id: int
    realm_users: list[dict]


@dataclass
class EventInfo:
    queue_id: str
    last_event_id: int


SLIM_CONFIG = dict(
    include_subscribers=json.dumps(False),
    client_gravatar=json.dumps(False),
    include_streams=json.dumps(False),
    user_list_incomplete=json.dumps(True),
)


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
