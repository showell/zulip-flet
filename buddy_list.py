import flet as ft

def buddy_list_item(user):
    item = ft.Row([
        ft.Image(src=user.avatar_url, height=17),
        ft.Text(user.name, color=ft.Colors.BLACK, size=17)
    ])

    return item

def make_buddy_list_container(database):
    items = []
    for user in sorted(database.user_dict.values(), key=lambda u: u.name):
        items.append(buddy_list_item(user))

    buddy_list = ft.ListView(items)
    buddy_list_container = ft.Container(
        buddy_list,
        border=ft.border.all(1, color=ft.Colors.BLUE),
        bgcolor=ft.Colors.LIGHT_BLUE_50,
        width=200,
        padding=10,
        alignment=ft.alignment.top_right,
        expand=True
    )
    return buddy_list_container
