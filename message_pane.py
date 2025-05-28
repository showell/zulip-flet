import flet as ft


async def message_row(service, message):
    sender = await service.get_user(message.sender_id)

    item = ft.Row(
        controls=[
            ft.Image(src=sender.avatar_url, height=30),
            ft.Column(
                controls=[
                    ft.Text(sender.name, size=14),
                    ft.Markdown(
                        message.content,
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

async def make_message_pane(service):
        items = []
        messages = await service.get_messages()
        for message in sorted(messages, key=lambda u: u.timestamp):
            items.append(await message_row(service, message))

        list_view = ft.ListView(items)
        list_container = ft.Container(
            list_view,
            bgcolor=ft.Colors.GREY_200,
            width=700,
            padding=10,
        )
        return list_container
