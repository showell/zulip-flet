import flet as ft


async def make_buddy_list_container(database):
    items = []
    for user in sorted(database.user_dict.values(), key=lambda u: u.name):
        items.append(ft.Text(user.name, color=ft.Colors.BLACK, size=17))

    buddy_list = ft.ListView(items)
    buddy_list_container = ft.Container(
        buddy_list,
        border=ft.border.all(1, color=ft.Colors.BLUE),
        bgcolor=ft.Colors.LIGHT_BLUE_50,
        width=160,
        padding=10,
        alignment=ft.alignment.top_right,
        expand=True
    )
    return buddy_list_container
