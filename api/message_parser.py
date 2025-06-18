from lxml import etree
from pydantic import BaseModel


class BaseNode(BaseModel):
    pass

    def as_text(self) -> str:
        return "UNKNOWN"


class RawNode(BaseNode):
    text: str

    def as_text(self) -> str:
        return self.text


class BodyNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return "".join(c.as_text() for c in self.children)


class TextNode(BaseNode):
    text: str

    def as_text(self) -> str:
        return self.text


class PNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return " ".join(c.as_text() for c in self.children) + "\n\n"


class UserMentionNode(BaseNode):
    name: str
    user_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ {'_' if self.silent else ''}{self.name} {self.user_id} ]"


def get_raw_node(elem: etree._Element) -> RawNode:
    return RawNode(text=etree.tostring(elem).decode("utf8"))


def get_p_node(elem: etree._Element) -> PNode:
    children: list[BaseNode] = []
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


def get_user_mention_node(elem: etree._Element, silent: bool) -> UserMentionNode:
    name = elem.text or ""
    user_id = elem.get("data-user-id") or ""
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


def get_node(elem: etree._Element) -> BaseNode:
    children = [get_node(c) for c in elem]
    if elem.tag == "html":
        return get_node(elem[0])
    elif elem.tag == "body":
        return BodyNode(children=children)
    elif elem.tag == "p":
        return get_p_node(elem)
    elif elem.tag == "span":
        elem_class = elem.get("class")
        if elem_class is None:
            return get_raw_node(elem)
        elif elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        elif elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)
        return get_raw_node(elem)
    else:
        return get_raw_node(elem)


def text_content(html: str) -> str:
    root = etree.HTML("<body>" + html + "</body>")
    return get_node(root).as_text()
