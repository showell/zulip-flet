import flet as ft
from message_list import MessageList


class MessagePane:
    def __init__(self, *, controller, width):
        self.message_list = MessageList(controller=controller, width=width)
        self.label = ft.Text("messages", height=40)
        self.control = ft.Column(
            controls=[self.label, self.message_list.control],
        )

    def populate_messages(self, hydrated_messages):
        self.message_list.populate_messages(hydrated_messages)
