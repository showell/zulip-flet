import sys

sys.path.append("api")

import flet as ft
import api.service as api


from buddy_list import make_buddy_list_container
from message_pane import MessagePane


async def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.window.height -= 50

    text = ft.Text(
        value="Loading",
        color=ft.Colors.RED,
    )

    page.add(text)
    page.update()

    service = await api.get_service()

    message_pane = MessagePane()

    buddy_list_container = await make_buddy_list_container(service)

    page.controls = [
        ft.Row(
            [
                message_pane.container,
                ft.VerticalDivider(width=3, thickness=1),
                buddy_list_container,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
    ]
    page.update()

    await message_pane.populate(service)


ft.app(main)
