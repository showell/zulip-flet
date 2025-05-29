import flet as ft


class BuddyListRow:
    def __init__(self, user, *, on_click_user):
        avatar = ft.Container(ft.Image(src=user.avatar_url, height=15))

        async def on_click(_):
            await on_click_user(user)

        avatar.on_click = on_click

        item = ft.Row(
            [
                avatar,
                ft.Text(user.name, color=ft.Colors.BLACK, size=15, selectable=True),
            ]
        )

        self.control = ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)
