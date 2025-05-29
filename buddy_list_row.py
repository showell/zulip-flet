import flet as ft


class BuddyListRow:
    def __init__(self, user):
        item = ft.Row(
            [
                ft.Image(src=user.avatar_url, height=15),
                ft.Text(user.name, color=ft.Colors.BLACK, size=15, selectable=True),
            ]
        )

        self.control = ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)
