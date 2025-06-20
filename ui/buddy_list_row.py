import flet as ft


class BuddyListRow:
    def __init__(self, user, *, controller):
        avatar = ft.Container(ft.Image(src=user.avatar_url, height=13))

        item = ft.Row(
            [
                avatar,
                ft.Text(user.name, color=ft.Colors.BLACK, size=13),
            ]
        )

        self.control = ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)

        async def on_click(_):
            await controller.populate_sent_by(user)

        self.control.on_click = on_click
