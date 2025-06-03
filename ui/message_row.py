import flet as ft


class AddressLink:
    def __init__(self, hydrated_message):
        self.control = ft.Text(
            hydrated_message.address_name,
            size=10,
            weight=ft.FontWeight.BOLD,
        )


class MessageRow:
    def populate(self, hydrated_message, *, width):
        sender = hydrated_message.deferred_sender.full_object()
        address_link = AddressLink(hydrated_message)

        item = ft.Row(
            controls=[
                ft.Image(src=sender.avatar_url, height=30),
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(sender.name, size=14),
                                address_link.control,
                            ],
                        ),
                        ft.Markdown(
                            hydrated_message.content,
                            selectable=True,
                            expand=True,
                            width=width,
                            auto_follow_links=True,
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
            padding=5,
            expand=True,
        )
