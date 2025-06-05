import flet as ft
from topic_list_row import TopicListRow


class TopicList:
    def __init__(self, *, controller, width):
        self.list_view = ft.ListView([], expand=True)
        self.control = ft.Container(
            self.list_view,
            width=width,
            padding=10,
            expand=True,
        )
        self.controller = controller
        self.width = width

    def populate(self, service):
        items = []
        topics = service.get_sorted_topics()
        for topic in topics:
            row = TopicListRow(
                topic,
                controller=self.controller,
                stream_table=service.database.stream_table,
                width=self.width - 30,
            )
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
