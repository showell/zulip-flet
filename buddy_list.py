import flet as ft


def buddy_list_item(user):
    item = ft.Row(
        [
            ft.Image(src=user.avatar_url, height=15),
            ft.Text(user.name, color=ft.Colors.BLACK, size=15, selectable=True),
        ]
    )

    return ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)


class BuddyList:
    def __init__(self):
        self.list_view = ft.ListView([], expand=True)
        self.control = ft.Container(
            self.list_view,
            width=350,
            padding=10,
            expand=True,
        )

    async def populate(self, service):
        items = []
        users = await service.get_users()
        for user in sorted(users, key=lambda u: u.name):
            items.append(buddy_list_item(user))

        self.list_view.controls = items
        self.list_view.update()
