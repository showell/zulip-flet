import flet as ft
from buddy_list import BuddyList
from message_list_config import MessageListConfig
from message_pane import MessagePane
from topic_list import TopicList


class ThreePane:
    def __init__(self, service):
        self.service = service
        self.topic_list = TopicList(controller=self, width=330)
        self.message_pane = MessagePane(controller=self, width=550)
        self.buddy_list = BuddyList(controller=self, width=150)

        self.control = ft.Row(
            [
                self.topic_list.control,
                ft.VerticalDivider(width=3, thickness=1),
                self.message_pane.control,
                ft.VerticalDivider(width=3, thickness=1),
                self.buddy_list.control,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    async def populate(self):
        self.buddy_list.populate(self.service)
        self.topic_list.populate(self.service)

    async def populate_sent_by(self, user):
        messages = await self.service.get_messages_sent_by_user(user)
        message_list_config = MessageListConfig(
            label=f"sent by {user.name}", show_sender=False
        )
        self.message_pane.populate_messages(
            message_list_config=message_list_config, hydrated_messages=messages
        )

    async def populate_for_direct_message(self, user):
        messages = await self.service.get_direct_messages_for_user(user)
        label = f"DMs with {user.name}"
        message_list_config = MessageListConfig(label=label, show_sender=True)
        self.message_pane.populate_messages(
            message_list_config=message_list_config, hydrated_messages=messages
        )

    async def populate_for_topic(self, topic):
        messages = await self.service.get_messages_for_topic(topic)
        label = topic.label(stream_table=self.service.database.stream_table)
        message_list_config = MessageListConfig(label=label, show_sender=True)
        self.message_pane.populate_messages(
            message_list_config=message_list_config, hydrated_messages=messages
        )

    async def populate_for_address(self, address):
        messages = await self.service.get_messages_for_address(address)
        label = address.name(
            stream_table=self.service.database.stream_table,
            topic_table=self.service.database.topic_table,
            user_table=self.service.database.user_table,
        )
        message_list_config = MessageListConfig(label=label, show_sender=True)
        self.message_pane.populate_messages(
            message_list_config=message_list_config, hydrated_messages=messages
        )
