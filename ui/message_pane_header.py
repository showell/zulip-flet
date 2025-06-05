import flet as ft


class MessagePaneHeader:
    def __init__(self):
        text = ft.Text("messages", height=30)
        self.control = ft.Row([text])

    def populate(self, *, message_list_config, participants):
        text = ft.Text(message_list_config.label, height=30)
        user_avatars = ft.Row([ft.Image(u.avatar_url, height=17) for u in participants])
        self.control.controls = [user_avatars, text]
        self.control.update()
