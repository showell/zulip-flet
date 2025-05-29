import sys

sys.path.append("api")

import flet as ft
import api.service as api
from api.config import HOST


from buddy_list import BuddyList
from message_pane import MessagePane


async def main(page: ft.Page):
    page.title = HOST
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

    async def populate_sent_by(user):
        await message_pane.populate_sent_by(service, user)

    message_pane = MessagePane()
    buddy_list = BuddyList(populate_sent_by=populate_sent_by)

    page.controls = [
        ft.Row(
            [
                message_pane.control,
                ft.VerticalDivider(width=3, thickness=1),
                buddy_list.control,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
    ]
    page.update()

    await buddy_list.populate(service)


ft.app(main)
