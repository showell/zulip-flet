from lxml import etree
from message_node import (
    AnchorNode,
    BaseNode,
    BlockQuoteNode,
    BodyNode,
    BreakNode,
    CodeNode,
    ContainerNode,
    DelNode,
    EmNode,
    EmojiImageNode,
    EmojiSpanNode,
    Header1Node,
    Header2Node,
    Header3Node,
    Header4Node,
    Header5Node,
    Header6Node,
    HrNode,
    InlineImageNode,
    InlineVideoNode,
    ListItemNode,
    MessageLinkNode,
    OrderedListNode,
    ParagraphNode,
    RawCodeBlockNode,
    RawKatexNode,
    RawNode,
    SpoilerNode,
    StreamLinkNode,
    StrongNode,
    TableNode,
    TBodyNode,
    TdNode,
    TextNode,
    THeadNode,
    ThNode,
    TimeWidgetNode,
    TrNode,
    UnorderedListNode,
    UserGroupMentionNode,
    UserMentionNode,
)


def text_content(elem: etree._Element) -> str:
    s = elem.text or ""
    for c in elem:
        s += text_content(c)
        s += c.tail or ""
    return s


"""
Custom validators follow.
"""


def get_code_block_node(elem: etree._Element) -> RawCodeBlockNode:
    html = etree.tostring(elem, with_tail=False).decode("utf-8")
    lang = elem.get("data-code-language") or "NOT SPECIFIED"
    content = text_content(elem)
    return RawCodeBlockNode(html=html, lang=lang, content=content)


def get_emoji_image_node(elem: etree._Element) -> EmojiImageNode:
    assert set(elem.attrib) == {"alt", "class", "src", "title"}
    alt = elem.get("alt")
    src = elem.get("src")
    title = elem.get("title")
    assert alt and src and title
    assert alt == f":{title.replace(' ', '_')}:"
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
    emoji_prefix, *unicodes = emoji_unicode_class.split("-")
    assert emoji_prefix == "emoji"
    assert unicodes
    assert elem.text == f":{title.replace(' ', '_')}:"
    assert len(list(elem.iterchildren())) == 0
    return EmojiSpanNode(title=title, unicodes=unicodes)


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

    if not set(grandchild.attrib).issubset(
        {
            "src",
            "data-animated",
            "data-original-dimensions",
            "data-original-content-type",
        }
    ):
        print(etree.tostring(elem).decode("utf8"))
        raise AssertionError()

    src = grandchild.get("src") or ""
    animated = (grandchild.get("data-animated") or "") == "true"
    original_dimensions = grandchild.get("data-original-dimensions") or ""
    original_content_type = grandchild.get("data-original-content-type") or ""
    assert src
    return InlineImageNode(
        href=href,
        title=title,
        src=src,
        animated=animated,
        original_dimensions=original_dimensions,
        original_content_type=original_content_type,
    )


def get_inline_video_node(elem: etree._Element) -> InlineVideoNode:
    assert set(elem.attrib) == {"class"}
    assert elem.get("class") == "message_inline_image message_inline_video"
    assert elem.text is None
    assert len(elem) == 1
    anchor = elem[0]
    assert anchor.tag == "a"
    assert set(anchor.attrib) == {"href", "title"}
    href = anchor.get("href") or ""
    title = anchor.get("title") or ""
    assert href and title
    assert len(anchor) == 1
    assert anchor.text is None
    video = anchor[0]
    assert video.tag == "video"
    assert set(video.attrib) == {"preload", "src"}
    assert video.get("preload") == "metadata"
    src = video.get("src") or ""
    assert src == href
    assert video.text is None
    return InlineVideoNode(href=href)


def get_message_link_node(elem: etree._Element) -> MessageLinkNode:
    assert set(elem.attrib) == {"class", "href"}
    href = elem.get("href") or ""
    assert href
    children = get_child_nodes(elem)
    return MessageLinkNode(
        href=href,
        children=children,
    )


def get_raw_katex_node(elem: etree._Element) -> RawKatexNode:
    assert set(elem.attrib) == {"class"}
    tag_class = elem.get("class") or ""
    assert tag_class in ["katex", "katex-display"]
    html = etree.tostring(elem, with_tail=False).decode("utf8")
    return RawKatexNode(html=html, tag_class=tag_class)


def get_raw_node(elem: etree._Element) -> RawNode:
    return RawNode(html=etree.tostring(elem, with_tail=False).decode("utf8"))


def get_spoiler_header(elem: etree._Element) -> BaseNode:
    assert set(elem.attrib) == {"class"}
    assert elem.get("class") == "spoiler-header"
    assert elem.text == "\n"
    if len(elem) == 0:
        return TextNode(text="")
    assert len(elem) == 1
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
    assert href and stream_id
    children = get_child_nodes(elem)
    return StreamLinkNode(
        href=href, stream_id=stream_id, children=children, has_topic=has_topic
    )


def table_cell_alignment(elem: etree._Element) -> str | None:
    assert set(elem.attrib).issubset({"style"})
    style = elem.get("style")
    if style is None:
        return None
    label, value = style.strip(";").split(": ")
    assert label == "text-align"
    assert value in ("center", "left", "right")
    return value


def get_table_node(elem: etree._Element) -> TableNode:
    def get_thead_node(thead: etree._Element) -> THeadNode:
        def get_th_node(th: etree._Element) -> ThNode:
            text_align = table_cell_alignment(th)
            children = get_child_nodes(th)
            return ThNode(text_align=text_align, children=children)

        assert len(thead) == 1
        tr = thead[0]
        assert tr.tag == "tr"
        ths = [get_th_node(th) for th in tr.iterchildren()]
        return THeadNode(ths=ths)

    def get_tbody_node(tbody: etree._Element) -> TBodyNode:
        def get_tr_node(tr: etree._Element) -> TrNode:
            def get_td_node(td: etree._Element) -> TdNode:
                text_align = table_cell_alignment(td)
                children = get_child_nodes(td)
                return TdNode(text_align=text_align, children=children)

            tds = [get_td_node(td) for td in tr.iterchildren()]
            return TrNode(tds=tds)

        trs = [get_tr_node(tr) for tr in tbody.iterchildren()]
        return TBodyNode(trs=trs)

    thead = get_thead_node(elem[0])
    tbody = get_tbody_node(elem[1])
    return TableNode(thead=thead, tbody=tbody)


def get_time_widget_node(elem: etree._Element) -> TimeWidgetNode:
    assert set(elem.attrib) == {"datetime"}
    datetime = elem.get("datetime") or ""
    assert datetime
    assert len(elem) == 0
    text = elem.text
    assert text
    return TimeWidgetNode(datetime=datetime, text=text)


def get_user_group_mention_node(
    elem: etree._Element, silent: bool
) -> UserGroupMentionNode:
    name = elem.text or ""
    assert set(elem.attrib) == {"class", "data-user-group-id"}
    group_id = elem.get("data-user-group-id") or ""
    assert group_id
    return UserGroupMentionNode(name=name, group_id=group_id, silent=silent)


def get_user_mention_node(elem: etree._Element, silent: bool) -> UserMentionNode:
    name = elem.text or ""
    assert set(elem.attrib) == {"class", "data-user-id"}
    user_id = elem.get("data-user-id") or ""
    assert user_id
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


def get_child_nodes(elem: etree._Element) -> list[BaseNode]:
    children: list[BaseNode] = []
    if elem.text:
        text = elem.text
        if text:
            children.append(TextNode(text=text))

    for c in elem:
        tail_text = c.tail or ""
        children.append(get_node(c))
        if tail_text:
            children.append(TextNode(text=tail_text))

    return children


def _get_node(elem: etree._Element) -> BaseNode:
    elem_class = elem.get("class") or ""

    if elem.tag == "a":
        if not elem_class:
            assert len(elem.attrib) == 1
            href = elem.get("href")
            assert href is not None
            return AnchorNode(href=href, children=get_child_nodes(elem))

        if elem_class == "message-link":
            return get_message_link_node(elem)

        if elem_class in ["stream", "stream-topic"]:
            return get_stream_link_node(elem)

    if elem.tag == "br":
        assert len(elem.attrib) == 0
        assert len(elem) == 0
        return BreakNode()

    if elem.tag == "div":
        if elem_class == "codehilite":
            return get_code_block_node(elem)
        if elem_class == "spoiler-block":
            return get_spoiler_node(elem)
        if elem_class == "message_inline_image":
            return get_inline_image_node(elem)
        if elem_class == "message_inline_image message_inline_video":
            return get_inline_video_node(elem)

    if elem.tag == "hr":
        assert len(elem.attrib) == 0
        assert len(elem) == 0
        return HrNode()

    if elem.tag == "img":
        if elem_class == "emoji":
            return get_emoji_image_node(elem)

    if elem.tag == "span":
        if elem_class.startswith("emoji "):
            return get_emoji_span_node(elem)
        if elem_class in ["katex", "katex-display"]:
            return get_raw_katex_node(elem)
        if elem_class == "user-group-mention":
            return get_user_group_mention_node(elem, silent=False)
        if elem_class == "user-group-mention silent":
            return get_user_group_mention_node(elem, silent=True)
        if elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        if elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)

    if elem.tag == "table":
        return get_table_node(elem)

    if elem.tag == "time":
        return get_time_widget_node(elem)

    simple_nodes: dict[str, type[ContainerNode]] = dict(
        body=BodyNode,
        blockquote=BlockQuoteNode,
        code=CodeNode,
        em=EmNode,
        h1=Header1Node,
        h2=Header2Node,
        h3=Header3Node,
        h4=Header4Node,
        h5=Header5Node,
        h6=Header6Node,
        li=ListItemNode,
        ol=OrderedListNode,
        p=ParagraphNode,
        strong=StrongNode,
        ul=UnorderedListNode,
    )

    # del is a keyword in Python
    simple_nodes["del"] = DelNode

    # XXX
    if elem.tag == "ol" and elem.get("start"):
        del elem.attrib["start"]

    if elem.tag in simple_nodes:
        if len(elem.attrib.keys()) > 0:
            print(etree.tostring(elem))
            raise Exception("Unknown attributes")
        return simple_nodes[elem.tag](children=get_child_nodes(elem))

    print("UNHANDLED", elem.tag)
    print(etree.tostring(elem))
    print()
    return get_raw_node(elem)


def get_node(elem: etree._Element) -> BaseNode:
    html = etree.tostring(elem, with_tail=False).decode("utf8")
    node = _get_node(elem)

    print()
    print(type(node), node)

    if not hasattr(node, "as_html"):
        print(node)
        raise AssertionError(f"need as_html for {type(node)}")

    if node.as_html() != html:
        print("\n------- as_html MISMATCH\n")
        print(repr(html))
        print()
        print(repr(node.as_html()))
        print()
        raise AssertionError("as_html is not precise")

    return node


def get_message_node(html: str) -> BaseNode:
    print(f"\nOUTER HMTL:\n{repr(html)}")
    root = etree.HTML("<body>" + html + "</body>")
    assert root.tag == "html"
    assert len(root) == 1
    body = root[0]
    assert body.tag == "body"
    message_node = get_node(body)
    return message_node
