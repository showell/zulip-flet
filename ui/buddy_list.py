import flet as ft
from buddy_list_row import BuddyListRow


class BuddyList:
    def __init__(self, *, controller, width):
        self.list_view = ft.ListView([], expand=True)
        self.control = ft.Container(
            self.list_view,
            width=width,
            padding=10,
            expand=True,
        )
        self.controller = controller

    def populate(self, service):
        items = []
        users = service.get_local_users()
        for user in sorted(users, key=lambda u: u.name):
            row = BuddyListRow(user, controller=self.controller)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
