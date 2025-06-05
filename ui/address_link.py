import flet as ft


class AddressLink:
    def __init__(self, hydrated_message, controller):
        text = ft.Text(
            hydrated_message.address_name,
            size=10,
            weight=ft.FontWeight.BOLD,
        )

        self.control = ft.Container(text)

        async def on_click(_):
            await controller.populate_for_address(hydrated_message.address)

        self.control.on_click = on_click
