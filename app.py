import flet as ft
from data_layer import get_database
from buddy_list import make_buddy_list_container
from message_pane import make_message_pane


async def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.window.height = 300
    page.window.top = 50

    text = ft.Text(
        value="Loading",
        color=ft.Colors.RED,
    )

    page.add(text)
    page.update()

    database = await get_database()

    message_pane_container = make_message_pane(database)
    buddy_list_container = make_buddy_list_container(database)

    page.controls = [
        ft.Row(
    [
                message_pane_container,
                ft.VerticalDivider(width=3, thickness=1),
                buddy_list_container,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        ),
    ]
    page.update()


ft.app(main)