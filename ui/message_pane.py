import flet as ft
from message_row import MessageRow


class MessagePane:
    def __init__(self, *, controller, width):
        self.list_view = ft.ListView([])

        self.control = ft.Container(
            self.list_view,
            bgcolor=ft.Colors.GREY_200,
            width=width,
            padding=10,
        )

        self.controller = controller

    def populate_messages(self, hydrated_messages):
        self.list_view.controls = []
        self.list_view.update()

        items = []

        for message in hydrated_messages:
            row = MessageRow(self.controller)
            row.populate(message, width=600)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
