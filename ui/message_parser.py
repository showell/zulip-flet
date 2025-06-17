from lxml import etree
from pydantic import BaseModel

class BaseNode(BaseModel):
    pass

class DumbNode(BaseNode):
    text: str
    children: list[BaseNode]

    def as_text(self):
        return self.text + "".join(c.as_text() for c in self.children)

def get_node(elem):
    text = elem.text or ""
    children = [get_node(c) for c in elem]
    return DumbNode(text=text, children=children)


def text_content(html):
    root = etree.HTML("<html>" + html + "</html>")
    return "raw: " + get_node(root).as_text()
