import flet as ft
from mypy.util import soft_wrap


class TopicListRow:
    def __init__(self, topic, *, controller, stream_table, width):
        item = ft.Row(
            [
                ft.Text(
                    topic.label(stream_table=stream_table),
                    color=ft.Colors.BLACK,
                    size=12,
                    width=width,
                ),
            ]
        )

        self.control = ft.Container(
            item, bgcolor=ft.Colors.LIGHT_BLUE_50, padding=5, width=width
        )
