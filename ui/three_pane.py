import flet as ft

from buddy_list import BuddyList
from message_pane import MessagePane
from topic_list import TopicList


class ThreePane:
    def __init__(self, service):
        self.service = service
        self.topic_list = TopicList(controller=self, width=330)
        self.message_pane = MessagePane(controller=self, width=500)
        self.buddy_list = BuddyList(controller=self, width=200)

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
        self.message_pane.populate_messages(messages)

    async def populate_for_address(self, address):
        messages = await self.service.get_messages_for_address(address)
        self.message_pane.populate_messages(messages)
