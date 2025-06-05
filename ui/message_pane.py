import flet as ft
from message_list import MessageList
from message_pane_header import MessagePaneHeader


class MessagePane:
    def __init__(self, *, controller, width):
        self.message_list = MessageList(controller=controller, width=width)
        self.header = MessagePaneHeader()
        self.control = ft.Column()
        self.control.controls = [self.header.control, self.message_list.control]

    def populate_messages(self, *, message_list_config, hydrated_messages):
        sender_dict = dict()
        for m in hydrated_messages:
            sender = m.deferred_sender.full_object()
            sender_dict[sender.id] = sender

        participants = sorted(sender_dict.values(), key=lambda u: u.name)
        self.header.populate(message_list_config=message_list_config, participants=participants)
        self.message_list.populate_messages(hydrated_messages, message_list_config)
        self.control.controls = [self.header.control, self.message_list.control]
        self.control.update()
