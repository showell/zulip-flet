import flet as ft
from data_layer import get_database
from buddy_list import make_buddy_list_container

async def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.window.height = 500
    page.window.top = 50

    text = ft.Text(
        value="Loading",
        color=ft.Colors.RED,
    )

    page.add(text)
    page.update()

    database = await get_database()

    buddy_list_container = await make_buddy_list_container(database)
    page.controls = [buddy_list_container]
    page.update()


ft.app(main)