import flet as ft
from message_row import MessageRow


class MessageList:
    def __init__(self, *, controller, width):
        self.list_view = ft.ListView([])

        self.control = ft.Container(
            self.list_view,
            bgcolor=ft.Colors.GREY_200,
            width=width,
            padding=10,
            expand=True,
        )

        self.controller = controller
        self.width = width

    def populate_messages(self, hydrated_messages, message_list_config):
        self.list_view.controls = []
        self.list_view.update()

        items = []

        for message in hydrated_messages:
            row = MessageRow(
                controller=self.controller, message_list_config=message_list_config
            )
            row.populate(message, width=self.width - 100)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
