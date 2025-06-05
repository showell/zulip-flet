import flet as ft


class MessagePaneHeaderAvatar:
    def __init__(self, user, *, controller):
        self.control = ft.Container(
            ft.Image(user.avatar_url, tooltip=user.name, height=30)
        )

        async def on_click(_):
            await controller.populate_for_direct_message(user)

        self.control.on_click = on_click
