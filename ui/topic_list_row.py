import flet as ft


class TopicListRow:
    def __init__(self, topic, *, controller, stream_table, width):
        item = ft.Row(
            [
                ft.Text(
                    topic.label(stream_table=stream_table),
                    color=ft.Colors.BLACK,
                    size=12,
                    selectable=True,
                ),
            ]
        )

        self.control = ft.Container(
            item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5, width=width
        )
