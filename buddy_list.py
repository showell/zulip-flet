import flet as ft

def buddy_list_item(user):
    item = ft.Row([
        ft.Image(src=user.avatar_url, height=15),
        ft.Text(user.name, color=ft.Colors.BLACK, size=15, selectable=True),
    ])

    return ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)

def make_buddy_list_container(database):
    items = []
    for user in sorted(database.user_dict.values(), key=lambda u: u.name):
        items.append(buddy_list_item(user))

    buddy_list = ft.ListView(items, expand=True)
    buddy_list_container = ft.Container(
        buddy_list,
        width=200,
        padding=10,
        expand=True,
    )
    return buddy_list_container
