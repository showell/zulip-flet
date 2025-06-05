import flet as ft


class MessagePaneHeader:
    def __init__(self):
        self.text = ft.Text("messages", height=30)
        self.control = ft.Row([self.text])

    def populate(self, *, message_list_config):
        self.text = ft.Text(message_list_config.label, height=30)
        self.control.controls = [self.text]
        self.control.update()
