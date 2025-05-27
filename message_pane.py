import flet as ft


async def message_row(database, message):
    sender = await database.get_user(message.sender_id)

    item = ft.Row(
        controls=[
            ft.Image(src=sender.avatar_url, height=30),
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

    def press(_):
        print("pressed")

    return ft.Container(item, padding=4, on_long_press=press)


async def make_message_pane(database):
    items = []
    for user in sorted(database.message_dict.values(), key=lambda u: u.timestamp):
        items.append(await message_row(database, user))

    list_view = ft.ListView(items)
    list_container = ft.Container(
        list_view,
        bgcolor=ft.Colors.GREY_200,
        width=700,
        padding=10,
    )
    return list_container
