import sys

sys.path.append("api")

import flet as ft
import api.service as api
from api.config import HOST
from three_pane import ThreePane


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

    three_pane = ThreePane(service)
    page.add(three_pane.control)
    await three_pane.populate()
    page.update()

if __name__ == "__main__":
    ft.app(main)