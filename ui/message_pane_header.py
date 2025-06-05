import flet as ft
from message_pane_header_avatar import MessagePaneHeaderAvatar


class MessagePaneHeader:
    def __init__(self, *, controller):
        text = ft.Text("messages", height=30)
        self.control = ft.Row([text])
        self.controller = controller

    def populate(self, *, message_list_config, participants):
        text = ft.Text(message_list_config.label, height=30)
        user_avatars = ft.Row(
            [
                MessagePaneHeaderAvatar(user, controller=self.controller).control
                for user in participants
            ]
        )
        self.control.controls = [user_avatars, text]
        self.control.update()
