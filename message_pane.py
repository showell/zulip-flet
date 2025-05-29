import flet as ft
from message_row import MessageRow

class MessagePane:
    def __init__(self):
        self.list_view = ft.ListView([], auto_scroll=True)

        self.control = ft.Container(
            self.list_view,
            bgcolor=ft.Colors.GREY_200,
            width=700,
            padding=10,
        )

    async def populate(self, service, user):
        self.list_view.controls = []
        self.list_view.update()

        items = []
        messages = await service.get_messages()
        for message in sorted(messages, key=lambda u: u.timestamp):
            if message.sender_id == user.id:
                row = MessageRow()
                await row.populate(service, message, width=600)
                items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
