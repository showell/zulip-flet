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


class TextNode(BaseNode):
    text: str

    def as_text(self):
        return self.text


class PNode(BaseNode):
    children: list[BaseNode]

    def as_text(self):
        return "".join(c.as_text() for c in self.children) + "\n\n"


def get_p_node(elem):
    children = []
    if elem.text:
        text = elem.text.strip()
        if text:
            children.append(TextNode(text=text))

    for c in elem:
        children.append(get_node(c))
        if c.tail:
            text = c.tail.strip()
            if text:
                children.append(TextNode(text=text))

    return PNode(children=children)


def get_node(elem):
    text = elem.text or ""
    children = [get_node(c) for c in elem]
    if elem.tag == "html":
        return get_node(elem[0])
    elif elem.tag == "body":
        return BodyNode(children=children)
    elif elem.tag == "p":
        return get_p_node(elem)
    else:
        return DumbNode(tag=elem.tag, text=text, children=children)


def text_content(html):
    root = etree.HTML("<body>" + html + "</body>")
    return get_node(root).as_text()
