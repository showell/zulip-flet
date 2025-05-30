import flet as ft


class MessageRow:
    def populate(self, service, hydrated_message, *, width):
        sender = hydrated_message.deferred_sender.full_object()

        item = ft.Row(
            controls=[
                ft.Image(src=sender.avatar_url, height=30),
                ft.Column(
                    controls=[
                        ft.Text(sender.name, size=14),
                        ft.Markdown(
                            hydrated_message.content,
                            selectable=True,
                            expand=True,
                            width=width,
                            auto_follow_links=True,
                        ),
                        ft.Text(hydrated_message.timestamp, size=9),
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
