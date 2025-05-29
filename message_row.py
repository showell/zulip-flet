import flet as ft


class MessageRow:
    async def populate(self, service, message, *, width):
        sender = await service.get_user(message.sender_id)

        item = ft.Row(
            controls=[
                ft.Image(src=sender.avatar_url, height=30),
                ft.Column(
                    controls=[
                        ft.Text(sender.name, size=14),
                        ft.Markdown(
                            message.content,
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
