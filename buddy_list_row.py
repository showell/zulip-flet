import flet as ft


class BuddyListRow:
    def __init__(self, user, *, populate_sent_by):
        avatar = ft.Container(ft.Image(src=user.avatar_url, height=15))

        item = ft.Row(
            [
                avatar,
                ft.Text(user.name, color=ft.Colors.BLACK, size=15, selectable=True),
            ]
        )

        self.control = ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)

        async def on_click(_):
            await populate_sent_by(user)

        self.control.on_click = on_click
