import flet as ft
from three_pane import ThreePane

import api.service as api
from api.config import HOST


async def main(page: ft.Page):
    page.title = HOST
    page.vertical_alignment = "center"
    page.horizontal_alignment = "center"
    page.window.height -= 50

    page.theme = ft.Theme(scrollbar_theme=ft.ScrollbarTheme(thumb_visibility=True))

    text = ft.Text(
        value="Loading",
        color=ft.Colors.RED,
    )

    page.add(text)
    page.update()

    service = await api.get_service()

    three_pane = ThreePane(service)
    page.controls = [three_pane.control]
    page.update()
    await three_pane.populate()
