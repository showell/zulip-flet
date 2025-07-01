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
    EmojiImageNode,
    EmojiSpanNode,
    InlineImageNode,
    ListItemNode,
    OrderedListNode,
    ParagraphNode,
    RawNode,
    SpoilerNode,
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


def get_emoji_image_node(elem: etree._Element) -> EmojiImageNode:
    assert set(elem.attrib) == {"alt", "class", "src", "title"}
    alt = elem.get("alt")
    src = elem.get("src")
    title = elem.get("title")
    assert alt and src and title
    assert alt == f":{title}:"
    return EmojiImageNode(src=src, title=title)


def get_emoji_span_node(elem: etree._Element) -> EmojiSpanNode:
    assert set(elem.attrib) == {"aria-label", "class", "role", "title"}
    title = elem.get("title") or ""
    assert title
    assert elem.get("role") == "img"
    assert elem.get("aria-label") == title
    elem_class = elem.get("class") or ""
    assert elem_class.startswith("emoji ")
    _, emoji_unicode_class = elem_class.split(" ")
    emoji_prefix, unicode = emoji_unicode_class.split("-")
    assert emoji_prefix == "emoji"
    assert elem.text == f":{title.replace(' ', '_')}:"
    assert len(list(elem.iterchildren())) == 0
    return EmojiSpanNode(title=title, unicode=unicode)


def get_raw_node(elem: etree._Element) -> RawNode:
    return RawNode(text=etree.tostring(elem, with_tail=False).decode("utf8"))


def get_inline_image_node(elem: etree._Element) -> InlineImageNode:
    assert set(elem.attrib) == {"class"}
    assert elem.get("class") == "message_inline_image"
    assert len(elem) == 1
    child = elem[0]
    assert child.tag == "a"
    assert set(child.attrib).issubset({"href", "title"})
    href = child.get("href") or ""
    title = child.get("title") or ""
    assert href
    assert len(child) == 1
    grandchild = child[0]
    assert grandchild.tag == "img"
    assert set(grandchild.attrib).issubset(
        {"src", "data-original-dimensions", "data-original-content-type"}
    )
    src = grandchild.get("src") or ""
    original_dimensions = grandchild.get("data-original-dimensions") or ""
    original_content_type = grandchild.get("data-original-content-type") or ""
    assert src
    return InlineImageNode(
        href=href,
        title=title,
        src=src,
        original_dimensions=original_dimensions,
        original_content_type=original_content_type,
    )


def get_spoiler_header(elem: etree._Element) -> BaseNode:
    assert set(elem.attrib) == {"class"}
    assert elem.get("class") == "spoiler-header"
    assert len(elem) == 1
    assert elem.text == "\n"
    para = elem[0]
    assert para.tag == "p"
    assert para.tail == "\n"
    para.tail = ""
    return get_node(para)


def get_spoiler_content(elem: etree._Element) -> BaseNode:
    assert elem.tag == "div"
    assert set(elem.attrib) == {"class", "aria-hidden"}
    assert elem.get("class") == "spoiler-content"
    assert elem.get("aria-hidden") == "true"
    assert elem.text == "\n"
    content = elem[0]
    assert content.tail == "\n"
    content.tail = ""
    return get_node(content)


def get_spoiler_node(elem: etree._Element) -> SpoilerNode:
    children = list(elem.iterchildren())
    assert len(children) == 2
    header = get_spoiler_header(children[0])
    content = get_spoiler_content(children[1])
    return SpoilerNode(header=header, content=content)


def get_stream_link_node(elem: etree._Element) -> StreamLinkNode:
    has_topic = elem.get("class") == "stream-topic"
    assert set(elem.attrib) == {"class", "data-stream-id", "href"}
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

    elem_class = elem.get("class") or ""

    if elem.tag == "a":
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
        if elem_class == "codehilite":
            return get_code_block_node(elem)
        if elem_class == "spoiler-block":
            return get_spoiler_node(elem)
        if elem_class == "message_inline_image":
            return get_inline_image_node(elem)

    if elem.tag == "img":
        if elem_class == "emoji":
            return get_emoji_image_node(elem)

    if elem.tag == "span":
        if elem_class.startswith("emoji "):
            return get_emoji_span_node(elem)
        if elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        if elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)

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
