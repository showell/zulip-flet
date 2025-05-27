import flet as ft


def message_row(message):
    item = ft.Row(
        controls=[
            ft.Text(
                message.content[:50],
                color=ft.Colors.BLACK, size=13,
                overflow=ft.TextOverflow.ELLIPSIS,
                selectable=True,
            ),
        ],
        width=300,
    )

    return item


def make_message_pane(database):
    items = []
    for user in sorted(database.message_dict.values(), key=lambda u: u.timestamp):
        items.append(message_row(user))

    list = ft.ListView(items)
    list_container = ft.Container(
        list,
        bgcolor=ft.Colors.GREY_50,
        width=300,
        padding=10,
    )
    return list_container
