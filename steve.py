import asyncio
from idlelib.rpc import response_queue

import aiohttp

class ZulipApi:
    def __init__(self, user_name, api_key):
        self.auth = aiohttp.BasicAuth(user_name, api_key)

    async def get(self, url_ending, handler):
        async with aiohttp.ClientSession() as session:
            url = "https://chat.zulip.org/api/v1/" + url_ending
            async with session.get(url, auth=self.auth) as response:
                await handler(response)

async def main():
    user_name="showell30@yahoo.com"
    api_key = "l7rVMet9LIolxUvBKHoXGcZGuGCjr2pm"
    zulip_api = ZulipApi(user_name, api_key)

    # WORKING
    async def handle_users(response):
        print("Status:", response.status)
        print("Content-type:", response.headers['content-type'])

        json = await response.text()
        print("\n\n\n\nBODY\n\n\n\n", json)


    await zulip_api.get("users", handle_users)

asyncio.run(main())