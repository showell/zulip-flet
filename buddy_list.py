import flet as ft
from buddy_list_row import BuddyListRow


class BuddyList:
    def __init__(self, *, on_click_user):
        self.list_view = ft.ListView([], expand=True)
        self.control = ft.Container(
            self.list_view,
            width=350,
            padding=10,
            expand=True,
        )
        self.on_click_user = on_click_user

    async def populate(self, service):
        items = []
        users = await service.get_users()
        for user in sorted(users, key=lambda u: u.name):
            row = BuddyListRow(user, on_click_user=self.on_click_user)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
