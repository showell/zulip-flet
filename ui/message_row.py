import flet as ft
from address_link import AddressLink


class MessageRow:
    def __init__(self, *, controller, message_list_config):
        self.controller = controller
        self.message_list_config = message_list_config

    def populate(self, hydrated_message, *, width):
        sender = hydrated_message.deferred_sender.full_object()
        address_link = AddressLink(hydrated_message, self.controller)

        if self.message_list_config.show_sender:
            info = ft.Text(sender.name, size=14, weight=ft.FontWeight.BOLD)
        else:
            info = address_link.control

        item = ft.Row(
            controls=[
                ft.Image(src=sender.avatar_url, tooltip=sender.name, height=30),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[info],
                        ),
                        ft.Text(
                            hydrated_message.content,
                            selectable=True,
                            expand=True,
                            width=width,
                            # auto_follow_links=True,
                        ),
                    ]
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
            expand=True,
        )

        self.control = ft.Container(
            item,
            border=ft.border.all(1, ft.Colors.GREY_200),
            padding=7,
            expand=True,
        )
