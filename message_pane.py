import flet as ft


async def message_row(database, message):
    sender = await database.get_user(message.sender_id)

    item = ft.Row(
        controls=[
            ft.Image(src=sender.avatar_url, height=30),
            ft.Column(
                controls=[
                    ft.Text(sender.name, size=14),
                    ft.Text(
                        message.content,
                        color=ft.Colors.BLACK,
                        bgcolor=ft.Colors.GREY_200,
                        size=13,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        selectable=True,
                        expand=True,
                    ),
                    ft.Text("need emojis still", size=3, text_align=ft.TextAlign.RIGHT),
                ]
            )
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
        expand=True,
    )

    return ft.Container(
        item,
        border=ft.border.all(1, ft.Colors.RED_100),
        padding=5,
        expand=True,
    )

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
