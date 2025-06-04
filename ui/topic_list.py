import flet as ft
from topic_list_row import TopicListRow


class TopicList:
    def __init__(self, *, controller):
        self.list_view = ft.ListView([], expand=True)
        self.control = ft.Container(
            self.list_view,
            width=250,
            padding=10,
            expand=True,
        )
        self.controller = controller

    def populate(self, service):
        items = []
        topics = service.get_sorted_topics()
        for topic in topics:
            row = TopicListRow(topic, controller=self.controller)
            items.append(row.control)

        self.list_view.controls = items
        self.list_view.update()
