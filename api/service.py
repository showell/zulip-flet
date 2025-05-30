import data_layer
from database import Database
from deferred_user import DeferredUserFactory
from user import User
from hydrated_message import HydratedMessage


class Service:
    def __init__(self, database: Database):
        self.database = database

    async def get_remote_users(self, user_ids: set[int]) -> dict[int, User]:
        user_dict = {}
        for user_id in user_ids:
            user_dict[user_id] = self.get_local_user(user_id)
        return user_dict

    def get_local_users(self) -> list[User]:
        return self.database.user_table.get_rows()

    def get_local_user(self, user_id: int) -> User:
        return self.database.user_table.get_row(user_id)

    async def get_messages_sent_by_user(self, user: User) -> list[HydratedMessage]:
        all_messages = self.database.message_table.get_rows()
        messages = [m for m in all_messages if m.sender_id == user.id]
        factory = DeferredUserFactory()
        hydrated_messages = [
            HydratedMessage.create(message=m, factory=factory) for m in messages
        ]
        await factory.finalize(service=self)
        return sorted(hydrated_messages, key=lambda m: m.timestamp)


async def get_service() -> Service:
    database = await data_layer.get_database()
    return Service(database)
