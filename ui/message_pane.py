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

    async def populate_sent_by(self, service, user):
        self.list_view.controls = []
        self.list_view.update()
        messages = await service.get_messages_sent_by_user(user)
        self.populate_messages(service, messages)

    def populate_messages(self, service, hydrated_messages):
        items = []

        for message in hydrated_messages:
            row = MessageRow()
            row.populate(message, width=600)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
