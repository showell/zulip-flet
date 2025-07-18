from html_helpers import SafeHtml, escape_text
from lxml import etree
from pydantic import BaseModel


class Element(BaseModel):
    html: SafeHtml


class TextElement(Element):
    text: str

    @staticmethod
    def from_text(text: str) -> "TextElement":
        return TextElement(
            html=escape_text(text),
            text=text,
        )


class TagElement(Element):
    tag: str
    attrib: dict[str, str]
    children: list["Element"]

    def get(self, field: str) -> str | None:
        return self.attrib.get(field)

    @staticmethod
    def from_lxml(elem: etree._Element) -> "TagElement":
        children: list["Element"] = []

        if elem.text is not None:
            children.append(TextElement.from_text(elem.text))

        for c in elem.iterchildren():
            children.append(TagElement.from_lxml(c))

            if c.tail is not None:
                children.append(TextElement.from_text(c.tail))

        return TagElement(
            html=SafeHtml.trust(etree.tostring(elem, with_tail=False).decode("utf-8")),
            tag=elem.tag,
            attrib={str(k): str(v) for k, v in elem.attrib.items()},
            children=children,
        )


class IllegalMessage(Exception):
    pass


def ensure_attribute(elem: TagElement, field: str, expected: str) -> None:
    ensure_equal(get_string(elem, field), expected)


def ensure_class(elem: TagElement, expected: str) -> None:
    ensure_equal(get_string(elem, "class"), expected)


def ensure_contains_text(elem: TagElement, expected: str) -> None:
    if len(elem.children) != 1:
        raise IllegalMessage(f"{elem.tag} should have only one child")
    child = elem.children[0]
    if not isinstance(child, TextElement):
        raise IllegalMessage(f"{elem.tag} has unexpected non-text children")
    ensure_equal(child.text, expected)


def ensure_empty(elem: TagElement) -> None:
    if len(elem.children) > 0:
        raise IllegalMessage(f"{elem} is not empty")


def ensure_equal(s1: str, s2: str) -> None:
    if s1 != s2:
        print(repr(s1))
        print(repr(s2))
        raise IllegalMessage(f"{s1} != {s2}")


def ensure_newline(elem: Element) -> None:
    if not isinstance(elem, TextElement):
        raise IllegalMessage("expected newline for pretty HTML")
    if elem.text != "\n":
        raise IllegalMessage("expected newline for pretty HTML")


def ensure_num_children(elem: TagElement, count: int) -> None:
    if len(elem.children) != count:
        raise IllegalMessage("bad count")


def ensure_tag(elem: TagElement, tag: str) -> None:
    ensure_equal(elem.tag, tag)


def ensure_tag_element(elem: Element) -> TagElement:
    if isinstance(elem, TagElement):
        return elem
    raise IllegalMessage(f"{elem} is not a tag")


def ensure_only_text(elem: TagElement) -> str:
    if len(elem.children) != 1:
        raise IllegalMessage(f"{elem.tag} has unexpected number of children")
    child = elem.children[0]
    if not isinstance(child, TextElement):
        raise IllegalMessage("text is missing")
    return child.text


def forbid_children(elem: TagElement) -> None:
    if len(elem.children) != 0:
        raise IllegalMessage(f"{elem.tag} has unexpected children")


def get_bool(elem: TagElement, field: str) -> bool:
    val = elem.get(field)
    if val is None:
        return False
    return val == "true"


def get_class(elem: TagElement, *expected: str) -> str:
    tag_class = get_string(elem, "class")
    if tag_class not in expected:
        raise IllegalMessage(f"unknown class {tag_class}")
    return tag_class


def get_trusted_html(elem: Element) -> SafeHtml:
    return elem.html


def get_database_id(elem: TagElement, field: str) -> int:
    s = get_string(elem, field)
    try:
        return int(s)
    except ValueError:
        raise IllegalMessage("not valid int")


def get_only_child(elem: TagElement, tag_name: str) -> TagElement:
    ensure_num_children(elem, 1)
    child = elem.children[0]
    if isinstance(child, TagElement):
        ensure_equal(child.tag, tag_name)
        return child

    raise IllegalMessage("unexpected text")


def get_only_block_child(elem: TagElement, tag_name: str) -> TagElement:
    ensure_num_children(elem, 3)
    ensure_newline(elem.children[0])
    child = ensure_tag_element(elem.children[1])
    ensure_newline(elem.children[2])
    ensure_equal(child.tag, tag_name)
    return child


def get_optional_int(elem: TagElement, field: str) -> int | None:
    val = maybe_get_string(elem, field)
    if val is None:
        return None
    return int(val)


def get_string(elem: TagElement, field: str, allow_empty: bool = False) -> str:
    s = maybe_get_string(elem, field)
    if s is None:
        raise IllegalMessage(f"{field} is missing")
    if s == "" and not allow_empty:
        raise IllegalMessage(f"{field} is empty string")
    return s


def get_tag_children(elem: TagElement) -> list[TagElement]:
    children: list[TagElement] = []

    for c in elem.children:
        if isinstance(c, TagElement):
            children.append(c)
        elif isinstance(c, TextElement):
            ensure_newline(c)

    return children


def get_two_children(elem: TagElement) -> tuple[TagElement, TagElement]:
    ensure_num_children(elem, 2)
    return ensure_tag_element(elem.children[0]), ensure_tag_element(elem.children[1])


def get_two_block_children(elem: TagElement) -> tuple[TagElement, TagElement]:
    ensure_num_children(elem, 5)
    ensure_newline(elem.children[0])
    c1 = ensure_tag_element(elem.children[1])
    ensure_newline(elem.children[2])
    c2 = ensure_tag_element(elem.children[3])
    ensure_newline(elem.children[4])
    return c1, c2


def maybe_get_string(elem: TagElement, field: str) -> str | None:
    return elem.get(field)


def restrict(elem: TagElement, tag: str, *fields: str) -> None:
    ensure_equal(elem.tag or "", tag)
    restrict_attributes(elem, *fields)


def restrict_attributes(elem: TagElement, *fields: str) -> None:
    if not set(elem.attrib).issubset(set(fields)):
        print(elem.html)
        raise IllegalMessage(
            f"{set(elem.attrib)} (actual attributes) > {set(fields)} (expected)"
        )


def text_content(elem: TagElement) -> str:
    s = ""
    for c in elem.children:
        if isinstance(c, TextElement):
            s += c.text
        elif isinstance(c, TagElement):
            s += text_content(c)
    return s
