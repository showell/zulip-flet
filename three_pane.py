import flet as ft

from buddy_list import BuddyList
from message_pane import MessagePane


class ThreePane:
    def __init__(self, service):
        self.service = service
        self.message_pane = MessagePane()
        self.buddy_list = BuddyList(populate_sent_by=self.populate_sent_by)

        self.control = ft.Row(
            [
                self.message_pane.control,
                ft.VerticalDivider(width=3, thickness=1),
                self.buddy_list.control,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )

    async def populate(self):
        await self.buddy_list.populate(self.service)

    async def populate_sent_by(self, user):
        await self.message_pane.populate_sent_by(self.service, user)
