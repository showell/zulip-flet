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


class BlockQuoteNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        content = "".join(c.as_text() for c in self.children)
        return f"\n-----\n{content}\n-----\n"


class BodyNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return "".join(c.as_text() for c in self.children)


class CodeBlockNode(BaseNode):
    lang: str
    content: str

    def as_text(self) -> str:
        return f"\n~~~~~~~~ lang: {self.lang}\n{self.content}~~~~~~~~\n"


class TextNode(BaseNode):
    text: str

    def as_text(self) -> str:
        print("use", self.text)
        return self.text


class ListItemNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return " ".join(c.as_text() for c in self.children)


class ParagraphNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return " ".join(c.as_text() for c in self.children) + "\n\n"


class StrongNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return f"**{''.join(c.as_text() for c in self.children)}**"


class UnorderedListNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)


class UserMentionNode(BaseNode):
    name: str
    user_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ {'_' if self.silent else ''}{self.name} {self.user_id} ]"


def text_content(elem: etree._Element) -> str:
    s = elem.text or ""
    for c in elem:
        s += text_content(c)
        s += c.tail or ""
    return s


def get_code_block_node(elem: etree._Element) -> CodeBlockNode:
    lang = elem.get("data-code-language") or "NOT SPECIFIED"
    content = text_content(elem)
    return CodeBlockNode(lang=lang, content=content)


def get_raw_node(elem: etree._Element) -> RawNode:
    return RawNode(text=etree.tostring(elem, with_tail=False).decode("utf8"))


def get_child_nodes(elem: etree._Element) -> list[BaseNode]:
    children: list[BaseNode] = []
    if elem.text:
        text = elem.text.strip()
        if text:
            children.append(TextNode(text=text))

    for c in elem:
        tail_text = (c.tail or "").strip()
        children.append(get_node(c))
        if tail_text:
            children.append(TextNode(text=tail_text))

    return children


def get_user_mention_node(elem: etree._Element, silent: bool) -> UserMentionNode:
    name = elem.text or ""
    user_id = elem.get("data-user-id") or ""
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


def get_node(elem: etree._Element) -> BaseNode:
    if elem.tag == "html":
        return get_node(elem[0])

    if elem.tag == "body":
        return BodyNode(children=get_child_nodes(elem))
    if elem.tag == "blockquote":
        return BlockQuoteNode(children=get_child_nodes(elem))
    if elem.tag == "li":
        return ListItemNode(children=get_child_nodes(elem))
    if elem.tag == "p":
        return ParagraphNode(children=get_child_nodes(elem))
    if elem.tag == "strong":
        return StrongNode(children=get_child_nodes(elem))
    if elem.tag == "ul":
        return UnorderedListNode(children=get_child_nodes(elem))

    if elem.tag == "div":
        elem_class = elem.get("class")
        if elem_class == "codehilite":
            return get_code_block_node(elem)
        return get_raw_node(elem)

    if elem.tag == "span":
        elem_class = elem.get("class")
        if elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        elif elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)
        return get_raw_node(elem)

    return get_raw_node(elem)


def message_text(html: str) -> str:
    root = etree.HTML("<body>" + html + "</body>")
    return get_node(root).as_text()
