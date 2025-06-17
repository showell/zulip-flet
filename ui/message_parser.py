from lxml import etree
from pydantic import BaseModel


def enclose(tag, inners):
    return f"<{tag}>{inners}</{tag}>"


class BaseNode(BaseModel):
    pass


class DumbNode(BaseNode):
    tag: str
    text: str
    children: list[BaseNode]

    def as_text(self):
        return enclose(
            self.tag, self.text + "".join(c.as_text() for c in self.children)
        )


class BodyNode(BaseNode):
    children: list[BaseNode]

    def as_text(self):
        return "".join(c.as_text() for c in self.children)


class PNode(BaseNode):
    text: str
    children: list[BaseNode]

    def as_text(self):
        return self.text + "".join(c.as_text() for c in self.children) + "\n\n"


def get_node(elem):
    text = elem.text or ""
    children = [get_node(c) for c in elem]
    if elem.tag == "html":
        return get_node(elem[0])
    elif elem.tag == "body":
        return BodyNode(children=children)
    elif elem.tag == "p":
        return PNode(text=text, children=children)
    else:
        return DumbNode(tag=elem.tag, text=text, children=children)


def text_content(html):
    root = etree.HTML("<body>" + html + "</body>")
    return get_node(root).as_text()
