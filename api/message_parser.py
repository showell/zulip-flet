from lxml import etree
from message_node import (
    AnchorNode,
    BaseNode,
    BlockQuoteNode,
    BodyNode,
    BreakNode,
    CodeBlockNode,
    CodeNode,
    ContainerNode,
    EmNode,
    ListItemNode,
    OrderedListNode,
    ParagraphNode,
    RawNode,
    StreamLinkNode,
    StrongNode,
    TextNode,
    UnorderedListNode,
    UserMentionNode,
)


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


def get_stream_link_node(elem: etree._Element) -> StreamLinkNode:
    has_topic = elem.get("class") == "stream-topic"
    assert set(elem.attrib.keys()) == {"class", "data-stream-id", "href"}
    stream_id = elem.get("data-stream-id") or ""
    href = elem.get("href") or ""
    text = elem.text or ""
    assert href and stream_id and text
    assert len(list(elem.iterchildren())) == 0
    return StreamLinkNode(
        href=href, stream_id=stream_id, text=text, has_topic=has_topic
    )


def get_user_mention_node(elem: etree._Element, silent: bool) -> UserMentionNode:
    name = elem.text or ""
    user_id = elem.get("data-user-id") or ""
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


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


def get_node(elem: etree._Element) -> BaseNode:
    if elem.tag == "html":
        return get_node(elem[0])

    if elem.tag == "a":
        elem_class = elem.get("class")
        if not elem_class:
            assert len(elem.attrib) == 1
            href = elem.get("href")
            assert href is not None
            return AnchorNode(href=href, children=get_child_nodes(elem))

        if elem_class in ["stream", "stream-topic"]:
            return get_stream_link_node(elem)

    if elem.tag == "br":
        assert len(elem.attrib) == 0
        return BreakNode()

    if elem.tag == "div":
        elem_class = elem.get("class")
        if elem_class == "codehilite":
            return get_code_block_node(elem)

    if elem.tag == "span":
        elem_class = elem.get("class")
        if elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        elif elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)
        return get_raw_node(elem)

    simple_nodes: dict[str, type[ContainerNode]] = dict(
        body=BodyNode,
        blockquote=BlockQuoteNode,
        code=CodeNode,
        em=EmNode,
        li=ListItemNode,
        ol=OrderedListNode,
        p=ParagraphNode,
        strong=StrongNode,
        ul=UnorderedListNode,
    )

    if elem.tag in simple_nodes:
        assert len(elem.attrib.keys()) == 0
        return simple_nodes[elem.tag](children=get_child_nodes(elem))

    print("UNHANDLED", elem.tag)
    print(etree.tostring(elem))
    print()
    return get_raw_node(elem)


def message_text(html: str) -> str:
    root = etree.HTML("<body>" + html + "</body>")
    return get_node(root).as_text()
