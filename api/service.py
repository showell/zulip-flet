import data_layer
from database import Database
from message import Message
from user import User


class Service:
    def __init__(self, database: Database):
        self.database = database

    async def get_users(self) -> list[User]:
        return self.database.user_table.get_rows()

    async def get_user(self, user_id: int) -> User:
        return self.database.user_table.get_row(user_id)

    async def get_messages(self) -> list[Message]:
        return self.database.message_table.get_rows()


async def get_service() -> Service:
    database = await data_layer.get_database()
    return Service(database)
