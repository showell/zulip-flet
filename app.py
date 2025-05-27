import asyncio

import flet as ft
from data_layer import get_database

async def main(page: ft.Page):
    page.title = "Flet counter example"
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.window.height = 300
    page.window.width = 500

    text = ft.Text(
        value="Loading",
        color=ft.Colors.RED,
    )

    page.add(text)
    page.update()

    database = await get_database()

    items = []
    for user in sorted(database.user_dict.values(), key=lambda u: u.name):
        items.append(ft.Text(user.name, color=ft.Colors.BLACK))

    buddy_list = ft.ListView(items)
    buddy_list_container = ft.Container(
        buddy_list,
        border =ft.border.all(1, color=ft.Colors.BLUE),
        bgcolor=ft.Colors.LIGHT_BLUE_50,
        width=200,
        alignment=ft.alignment.top_right,
        expand=True
    )
    page.controls = [buddy_list_container]
    page.update()

ft.app(main)