import flet as ft


def message_row(message):
    item = ft.Row(
        controls=[
            ft.Text(
                message.content,
                color=ft.Colors.BLACK,
                bgcolor=ft.Colors.GREY_200,
                size=13,
                overflow=ft.TextOverflow.ELLIPSIS,
                selectable=True,
                expand=True,
            ),
        ],
    )

    return ft.Container(item, padding=4)


def make_message_pane(database):
    items = []
    for user in sorted(database.message_dict.values(), key=lambda u: u.timestamp):
        items.append(message_row(user))

    list = ft.ListView(items)
    list_container = ft.Container(
        list,
        bgcolor=ft.Colors.GREY_200,
        width=700,
        padding=10,
    )
    return list_container
