import asyncio
import json
from config import HOST, USER_NAME, API_KEY
from database import Database
from event_info import EventInfo
from register import register, RegisterInfo
from zulip import ZulipApi

MESSAGE_BATCH_SIZE = 5_000


async def fetch_and_populate_messages(zulip_api: ZulipApi, database: Database) -> None:
    print("\n\n---------\n\n")
    print("FETCH MESSAGES (recent)")
    params = dict(
        anchor="newest",
        num_before=MESSAGE_BATCH_SIZE,
        client_gravatar=json.dumps(False),
        apply_markdown=json.dumps(False),
    )
    async with zulip_api.GET_json("messages", params) as data:
        database.populate_messages(data["messages"])


async def process_events(zulip_api: ZulipApi, event_info: EventInfo) -> None:
    def handle_event(event: object) -> None:
        print(event)

    await zulip_api.process_events(
        event_info=event_info,
        callback=handle_event,
    )


async def populate_database(
    zulip_api: ZulipApi, register_info: RegisterInfo
) -> Database:
    database = Database.create_empty_database()

    await fetch_and_populate_messages(zulip_api, database)

    # Make sure messages are already populated for these
    database.populate_users(HOST, register_info.realm_users)
    database.populate_streams(register_info.streams)

    return database


async def main() -> None:
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    register_info = await register(zulip_api)

    database = await populate_database(zulip_api, register_info)

    db_json = database.model_dump_json()
    fn = "database.json"
    with open(fn, "w", encoding="utf8") as database_file:
        database_file.write(db_json)
    print(f"Database saved to {fn}")


async def get_database() -> Database:
    fn = "database.json"
    with open(fn, encoding="utf8") as database_file:
        db_json = database_file.read()
    database = Database.model_validate_json(db_json)
    print(f"cached data loaded from {fn}")
    return database


async def original_main() -> None:
    zulip_api = ZulipApi(HOST, USER_NAME, API_KEY)
    register_info = await register(zulip_api)

    await populate_database(zulip_api, register_info)

    event_info = EventInfo(
        queue_id=register_info.queue_id,
        last_event_id=register_info.last_event_id,
    )

    await process_events(zulip_api, event_info)


if __name__ == "__main__":
    asyncio.run(main())
