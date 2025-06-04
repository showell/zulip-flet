import flet as ft


class TopicListRow:
    def __init__(self, topic, *, controller):
        item = ft.Row(
            [
                ft.Text(topic.name, color=ft.Colors.BLACK, size=15, selectable=True),
            ]
        )

        self.control = ft.Container(item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5)
