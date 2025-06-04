import flet as ft
from message_list import MessageList


class MessagePane:
    def __init__(self, *, controller, width):
        self.message_list = MessageList(controller=controller, width=width)
        self.label = ft.Text("messages", height=30)
        self.control = ft.Column()
        self.control.controls = [self.label, self.message_list.control]

    def populate_messages(self, *, message_list_config, hydrated_messages):
        self.label = ft.Text(message_list_config.label, height=30)
        self.message_list.populate_messages(hydrated_messages)
        self.control.controls = [self.label, self.message_list.control]
        self.control.update()
