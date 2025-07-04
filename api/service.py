import data_layer
from address import Address
from database import Database
from deferred_user import DeferredUserFactory, DeferredUserHelper
from filter import AddressFilter, DirectMessageFilter, SentByFilter, TopicFilter
from hydrated_message import HydratedMessage
from message import Message
from topic import Topic
from user import User


class Service:
    def __init__(self, database: Database):
        self.database = database

    async def get_remote_users(self, user_ids: set[int]) -> dict[int, User]:
        # TODO: Actually get remote users!  This function only exists
        # now to test out async logic.
        import asyncio

        await asyncio.sleep(2)
        user_dict = {}
        for user_id in user_ids:
            user_dict[user_id] = self.database.user_table.get_row(user_id)
        return user_dict

    def get_sorted_local_users(self) -> list[User]:
        users = self.database.user_table.get_rows()
        return sorted(
            users, key=lambda u: (u.id != self.database.current_user_id, u.name)
        )

    def get_sorted_topics(self) -> list[Topic]:
        return self.database.topic_table.get_sorted_rows(
            stream_table=self.database.stream_table
        )

    def maybe_get_local_user(self, user_id: int) -> User | None:
        return self.database.user_table.maybe_get_row(user_id)

    async def get_messages_sent_by_user(self, user: User) -> list[HydratedMessage]:
        all_messages = self.database.message_table.get_rows()
        messages = SentByFilter(user.id).get_rows(all_messages)
        return await self._get_hydrated_messages(messages)

    async def get_direct_messages_for_user(self, user: User) -> list[HydratedMessage]:
        all_messages = self.database.message_table.get_rows()
        messages = DirectMessageFilter(user_id=user.id).get_rows(all_messages)
        return await self._get_hydrated_messages(messages)

    async def get_messages_for_address(self, address: Address) -> list[HydratedMessage]:
        all_messages = self.database.message_table.get_rows()
        messages = AddressFilter(address).get_rows(all_messages)
        return await self._get_hydrated_messages(messages)

    async def get_messages_for_topic(self, topic: Topic) -> list[HydratedMessage]:
        all_messages = self.database.message_table.get_rows()
        topic_id = self.database.topic_table.get_id(topic)
        messages = TopicFilter(topic_id=topic_id).get_rows(all_messages)
        return await self._get_hydrated_messages(messages)

    async def _get_hydrated_messages(
        self, messages: list[Message]
    ) -> list[HydratedMessage]:
        factory = DeferredUserFactory()
        hydrated_messages = [
            HydratedMessage.create(message=m, factory=factory, database=self.database)
            for m in messages
        ]
        helper = DeferredUserHelper(
            maybe_get_local_user=self.maybe_get_local_user,
            get_remote_users=self.get_remote_users,
        )
        await factory.finalize(helper=helper)
        return sorted(hydrated_messages, key=lambda m: m.timestamp)


async def get_service() -> Service:
    database = await data_layer.get_database()
    return Service(database)
