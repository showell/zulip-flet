import flet as ft

class MessagePaneHeaderAvatar:
    def __init__(self, user):
        self.control = ft.Image(user.avatar_url, tooltip=user.name, height=30)
