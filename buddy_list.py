import flet as ft
from buddy_list_row import BuddyListRow


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
            items.append(BuddyListRow(user).control)

        self.list_view.controls = items
        self.list_view.update()
