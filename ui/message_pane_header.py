import flet as ft
from message_pane_header_avatar import MessagePaneHeaderAvatar

class MessagePaneHeader:
    def __init__(self):
        text = ft.Text("messages", height=30)
        self.control = ft.Row([text])

    def populate(self, *, message_list_config, participants):
        text = ft.Text(message_list_config.label, height=30)
        user_avatars = ft.Row(
            [MessagePaneHeaderAvatar(user).control for user in participants]
        )
        self.control.controls = [user_avatars, text]
        self.control.update()
