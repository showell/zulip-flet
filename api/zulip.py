from contextlib import asynccontextmanager
from dataclasses import asdict
from event_info import EventInfo
from typing import Any, AsyncGenerator, Callable

import aiohttp


class ZulipApi:
    def __init__(self, host: str, user_name: str, api_key: str) -> None:
        self.auth = aiohttp.BasicAuth(user_name, api_key)
        self.url_prefix = host + "/api/v1/"

    @asynccontextmanager
    async def post(
        self, url_ending: str, data: dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + url_ending
            async with session.post(url, auth=self.auth, data=data) as response:
                yield response

    @asynccontextmanager
    async def POST_json(
        self, url_ending: str, data: dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        async with self.post(url_ending, data) as response:
            assert response.status == 200
            yield await response.json()

    @asynccontextmanager
    async def get(
        self, url_ending: str, params: dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + url_ending
            async with session.get(url, auth=self.auth, params=params) as response:
                yield response

    @asynccontextmanager
    async def GET_json(
        self, url_ending: str, params: dict[str, Any]
    ) -> AsyncGenerator[Any, None]:
        for _ in range(5):
            async with self.get(url_ending, params) as response:
                if response.status == 200:
                    data = await response.json()
                    assert data["result"] == "success"
                    yield data
                    return
                else:
                    print(response.status)
                    print(response.text)
                    print(await response.json())
                    raise Exception("invalid response")

    async def process_events(
        self, *, event_info: EventInfo, callback: Callable[[dict[str, object]], None]
    ) -> None:
        async with aiohttp.ClientSession() as session:
            url = self.url_prefix + "events"
            print("WAITING FOR EVENTS (infinite loop)")
            while True:
                print("---> start new get")
                async with session.get(
                    url, auth=self.auth, params=asdict(event_info)
                ) as response:
                    assert response.status == 200
                    data = await response.json()
                    for event in data["events"]:
                        callback(event)
                        event_info.last_event_id = max(
                            event_info.last_event_id, event["id"]
                        )
