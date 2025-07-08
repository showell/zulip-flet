from html_helpers import SafeHtml
from lxml import etree
from message_node import (
    AnchorNode,
    BaseNode,
    BlockQuoteNode,
    BodyNode,
    BreakNode,
    CodeNode,
    DeleteNode,
    EmojiImageNode,
    EmojiSpanNode,
    EmphasisNode,
    HeadingNode,
    InlineImageChildImgNode,
    InlineImageNode,
    InlineVideoNode,
    KatexNode,
    ListItemNode,
    MessageLinkNode,
    OrderedListNode,
    ParagraphNode,
    PygmentsCodeBlockNode,
    SpoilerContentNode,
    SpoilerHeaderNode,
    SpoilerNode,
    StreamLinkNode,
    StrongNode,
    TableNode,
    TBodyNode,
    TdNode,
    TextNode,
    THeadNode,
    ThematicBreakNode,
    ThNode,
    TimeWidgetNode,
    TrNode,
    UnorderedListNode,
    UserGroupMentionNode,
    UserMentionNode,
)

Element = etree._Element


def assert_attribute(elem: Element, field: str, expected: str) -> None:
    assert_equal(elem.get(field) or "", expected)


def assert_class(elem: Element, expected: str) -> None:
    assert_equal(get_string(elem, "class"), expected)


def assert_contains_text(elem: Element, expected: str) -> None:
    assert_equal(elem.text or "", expected)
    if len(elem) != 0:
        print(etree.tostring(elem, with_tail=False))
        raise AssertionError(f"{elem.tag} has unexpected non-text children")


def assert_empty(elem: Element) -> None:
    if elem.text or len(elem) > 0:
        raise AssertionError(f"{elem} is not empty")


def assert_equal(s1: str, s2: str) -> None:
    if s1 != s2:
        print(repr(s1))
        print(repr(s2))
        raise AssertionError(f"{s1} != {s2}")


def assert_num_children(elem: Element, count: int) -> None:
    if len(elem) != count:
        raise AssertionError("bad count")


def forbid_children(elem: Element) -> None:
    assert elem.text is None
    if len(elem) != 0:
        print(etree.tostring(elem, with_tail=False))
        raise AssertionError(f"{elem.tag} has unexpected children")


def get_bool(elem: Element, field: str) -> bool:
    return (elem.get(field) or "") == "true"


def get_class(elem: Element, *expected: str) -> str:
    tag_class = get_string(elem, "class")
    if tag_class not in expected:
        raise AssertionError(f"unknown class {tag_class}")
    return tag_class


def get_html(elem: Element) -> str:
    return etree.tostring(elem, with_tail=False).decode("utf-8")


def get_only_child(elem: Element, tag_name: str) -> Element:
    assert_num_children(elem, 1)
    assert elem.text is None
    child = elem[0]
    assert child.tail is None
    assert_equal(child.tag, tag_name)
    return child


def get_optional_int(elem: Element, field: str) -> int | None:
    val = elem.get(field)
    return int(val) if val else None


def get_string(elem: Element, field: str) -> str:
    s = elem.get(field)
    if s is None:
        raise AssertionError(f"{field} is missing")
    return s


def get_two_children(elem: Element) -> tuple[Element, Element]:
    assert_num_children(elem, 2)
    assert elem.text is None
    for c in elem:
        assert c.tail is None
    return elem[0], elem[1]


def restrict(elem: Element, tag: str, *fields: str) -> None:
    assert_equal(elem.tag or "", tag)
    restrict_attributes(elem, *fields)


def restrict_attributes(elem: Element, *fields: str) -> None:
    if not set(elem.attrib).issubset(set(fields)):
        print(etree.tostring(elem, with_tail=False))
        raise AssertionError(
            f"{set(elem.attrib)} (actual attributes) > {set(fields)} (expected)"
        )


def text_content(elem: Element) -> str:
    s = elem.text or ""
    for c in elem:
        s += text_content(c)
        s += c.tail or ""
    return s


"""
Custom validators follow.
"""


def get_code_block_node(elem: Element) -> PygmentsCodeBlockNode:
    restrict(elem, "div", "class", "data-code-language")
    html = get_html(elem)
    lang = elem.get("data-code-language")
    content = text_content(elem)
    return PygmentsCodeBlockNode(html=SafeHtml.trust(html), lang=lang, content=content)


def get_emoji_image_node(elem: Element) -> EmojiImageNode:
    restrict(elem, "img", "alt", "class", "src", "title")
    alt = get_string(elem, "alt")
    src = get_string(elem, "src")
    title = get_string(elem, "title")
    assert_equal(alt, f":{title.replace(' ', '_')}:")
    return EmojiImageNode(src=src, title=title)


def get_emoji_span_node(elem: Element) -> EmojiSpanNode:
    restrict(elem, "span", "aria-label", "class", "role", "title")
    title = get_string(elem, "title")
    assert_attribute(elem, "role", "img")
    assert_attribute(elem, "aria-label", title)
    elem_class = get_string(elem, "class")
    assert elem_class.startswith("emoji ")
    _, emoji_unicode_class = elem_class.split(" ")
    emoji_prefix, *unicodes = emoji_unicode_class.split("-")
    assert_equal(emoji_prefix, "emoji")
    assert unicodes
    assert_contains_text(elem, f":{title.replace(' ', '_')}:")
    return EmojiSpanNode(title=title, unicodes=unicodes)


def get_img_node(elem: Element) -> InlineImageChildImgNode:
    restrict(
        elem,
        "img",
        "src",
        "data-animated",
        "data-original-dimensions",
        "data-original-content-type",
    )
    src = get_string(elem, "src")
    animated = get_bool(elem, "data-animated")
    original_dimensions = elem.get("data-original-dimensions")
    original_content_type = elem.get("data-original-content-type")
    return InlineImageChildImgNode(
        src=src,
        animated=animated,
        original_dimensions=original_dimensions,
        original_content_type=original_content_type,
    )


def get_katex_node(elem: Element) -> KatexNode:
    restrict(elem, "span", "class")
    tag_class = get_class(elem, "katex", "katex-display")
    html = get_html(elem)
    return KatexNode(html=SafeHtml.trust(html), tag_class=tag_class)


def get_inline_image_node(elem: Element) -> InlineImageNode:
    restrict(elem, "div", "class")
    assert_class(elem, "message_inline_image")
    anchor = get_only_child(elem, "a")
    restrict(anchor, "a", "href", "title")
    href = get_string(anchor, "href")
    title = anchor.get("title")
    img = get_only_child(anchor, "img")

    return InlineImageNode(
        img=get_img_node(img),
        href=href,
        title=title,
    )


def get_inline_video_node(elem: Element) -> InlineVideoNode:
    restrict(elem, "div", "class")
    assert_class(elem, "message_inline_image message_inline_video")

    anchor = get_only_child(elem, "a")

    restrict(anchor, "a", "href", "title")
    href = get_string(anchor, "href")
    title = anchor.get("title")

    video = get_only_child(anchor, "video")

    restrict(video, "video", "preload", "src")
    assert_attribute(video, "preload", "metadata")
    src = get_string(video, "src")
    assert_empty(video)

    return InlineVideoNode(href=href, src=src, title=title)


def get_list_item_node(elem: Element) -> ListItemNode:
    restrict(elem, "li")
    return ListItemNode(children=get_child_nodes(elem))


def get_list_item_nodes(elem: Element) -> list[ListItemNode]:
    children: list[ListItemNode] = []
    assert elem.text == "\n"

    for c in elem:
        assert c.tail in (None, "\n")
        children.append(get_list_item_node(c))

    return children


def get_ordered_list_node(elem: Element) -> OrderedListNode:
    restrict(elem, "ol", "start")
    start = get_optional_int(elem, "start")
    children = get_list_item_nodes(elem)
    return OrderedListNode(children=children, start=start)


def get_message_link_node(elem: Element) -> MessageLinkNode:
    restrict(elem, "a", "class", "href")
    href = get_string(elem, "href")
    children = get_child_nodes(elem)
    return MessageLinkNode(
        href=href,
        children=children,
    )


def get_spoiler_content(elem: Element) -> SpoilerContentNode:
    restrict(elem, "div", "class", "aria-hidden")
    assert_class(elem, "spoiler-content")
    assert_attribute(elem, "aria-hidden", "true")
    aria_attribute_comes_first = list(elem.attrib.keys())[0] == "aria-hidden"
    return SpoilerContentNode(
        children=get_child_nodes(elem, ignore_newlines=True),
        aria_attribute_comes_first=aria_attribute_comes_first,
    )


def get_spoiler_header(elem: Element) -> SpoilerHeaderNode:
    restrict(elem, "div", "class")
    assert_class(elem, "spoiler-header")
    return SpoilerHeaderNode(children=get_child_nodes(elem, ignore_newlines=True))


def get_spoiler_node(elem: Element) -> SpoilerNode:
    restrict(elem, "div", "class")
    assert_class(elem, "spoiler-block")
    header_elem, content_elem = get_two_children(elem)
    header = get_spoiler_header(header_elem)
    content = get_spoiler_content(content_elem)
    return SpoilerNode(header=header, content=content)


def get_stream_link_node(elem: Element) -> StreamLinkNode:
    has_topic = elem.get("class") == "stream-topic"
    assert set(elem.attrib) == {"class", "data-stream-id", "href"}
    stream_id = elem.get("data-stream-id") or ""
    href = elem.get("href") or ""
    assert href and stream_id
    children = get_child_nodes(elem)
    return StreamLinkNode(
        href=href, stream_id=stream_id, children=children, has_topic=has_topic
    )


def get_table_cell_alignment(elem: Element) -> str | None:
    assert set(elem.attrib).issubset({"style"})
    style = elem.get("style")
    if style is None:
        return None
    label, value = style.strip(";").split(": ")
    assert label == "text-align"
    assert value in ("center", "left", "right")
    return value


def get_table_node(elem: Element) -> TableNode:
    def get_thead_node(thead: Element) -> THeadNode:
        def get_th_node(th: Element) -> ThNode:
            text_align = get_table_cell_alignment(th)
            children = get_child_nodes(th)
            return ThNode(text_align=text_align, children=children)

        assert len(thead) == 1
        tr = thead[0]
        assert tr.tag == "tr"
        ths = [get_th_node(th) for th in tr.iterchildren()]
        return THeadNode(ths=ths)

    def get_tbody_node(tbody: Element) -> TBodyNode:
        def get_tr_node(tr: Element) -> TrNode:
            def get_td_node(td: Element) -> TdNode:
                text_align = get_table_cell_alignment(td)
                children = get_child_nodes(td)
                return TdNode(text_align=text_align, children=children)

            tds = [get_td_node(td) for td in tr.iterchildren()]
            return TrNode(tds=tds)

        trs = [get_tr_node(tr) for tr in tbody.iterchildren()]
        return TBodyNode(trs=trs)

    thead = get_thead_node(elem[0])
    tbody = get_tbody_node(elem[1])
    return TableNode(thead=thead, tbody=tbody)


def get_time_widget_node(elem: Element) -> TimeWidgetNode:
    assert set(elem.attrib) == {"datetime"}
    datetime = elem.get("datetime") or ""
    assert datetime
    assert len(elem) == 0
    text = elem.text
    assert text
    return TimeWidgetNode(datetime=datetime, text=text)


def get_unordered_list_node(elem: Element) -> UnorderedListNode:
    restrict_attributes(elem)
    children = get_list_item_nodes(elem)
    return UnorderedListNode(children=children)


def get_user_group_mention_node(elem: Element, silent: bool) -> UserGroupMentionNode:
    name = elem.text or ""
    assert set(elem.attrib) == {"class", "data-user-group-id"}
    group_id = elem.get("data-user-group-id") or ""
    assert group_id
    return UserGroupMentionNode(name=name, group_id=group_id, silent=silent)


def get_user_mention_node(elem: Element, silent: bool) -> UserMentionNode:
    name = elem.text or ""
    assert set(elem.attrib) == {"class", "data-user-id"}
    user_id = elem.get("data-user-id") or ""
    assert user_id
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


def get_child_nodes(elem: Element, ignore_newlines: bool = False) -> list[BaseNode]:
    children: list[BaseNode] = []
    if elem.text:
        text = elem.text
        if text and not (ignore_newlines and text == "\n"):
            children.append(TextNode(value=text))

    for c in elem:
        tail_text = c.tail or ""
        children.append(get_node(c))
        if tail_text and not (ignore_newlines and tail_text == "\n"):
            children.append(TextNode(value=tail_text))

    return children


def _get_node(elem: Element) -> BaseNode:
    elem_class = elem.get("class") or ""

    if elem.tag == "a":
        if elem_class == "message-link":
            return get_message_link_node(elem)

        if elem_class in ["stream", "stream-topic"]:
            return get_stream_link_node(elem)

        restrict_attributes(elem, "href")
        href = get_string(elem, "href")
        return AnchorNode(href=href, children=get_child_nodes(elem))

    if elem.tag == "blockquote":
        restrict_attributes(elem)
        return BlockQuoteNode(children=get_child_nodes(elem))

    if elem.tag == "body":
        restrict_attributes(elem)
        return BodyNode(children=get_child_nodes(elem))

    if elem.tag == "br":
        restrict_attributes(elem)
        forbid_children(elem)
        return BreakNode()

    if elem.tag == "code":
        restrict_attributes(elem)
        return CodeNode(children=get_child_nodes(elem))

    if elem.tag == "del":
        restrict_attributes(elem)
        return DeleteNode(children=get_child_nodes(elem))

    if elem.tag == "div":
        if elem_class == "codehilite":
            return get_code_block_node(elem)
        if elem_class == "spoiler-block":
            return get_spoiler_node(elem)
        if elem_class == "message_inline_image":
            return get_inline_image_node(elem)
        if elem_class == "message_inline_image message_inline_video":
            return get_inline_video_node(elem)

        raise AssertionError("unexpected class for div")

    if elem.tag == "em":
        restrict_attributes(elem)
        return EmphasisNode(children=get_child_nodes(elem))

    if elem.tag == "h1":
        return HeadingNode(depth=1, children=get_child_nodes(elem))

    if elem.tag == "h2":
        return HeadingNode(depth=2, children=get_child_nodes(elem))

    if elem.tag == "h3":
        return HeadingNode(depth=3, children=get_child_nodes(elem))

    if elem.tag == "h4":
        return HeadingNode(depth=4, children=get_child_nodes(elem))

    if elem.tag == "h5":
        return HeadingNode(depth=5, children=get_child_nodes(elem))

    if elem.tag == "h6":
        return HeadingNode(depth=6, children=get_child_nodes(elem))

    if elem.tag == "hr":
        restrict_attributes(elem)
        forbid_children(elem)
        return ThematicBreakNode()

    if elem.tag == "img":
        if elem_class == "emoji":
            return get_emoji_image_node(elem)

    if elem.tag == "ol":
        return get_ordered_list_node(elem)

    if elem.tag == "p":
        restrict_attributes(elem)
        return ParagraphNode(children=get_child_nodes(elem))

    if elem.tag == "span":
        if elem_class.startswith("emoji "):
            return get_emoji_span_node(elem)
        if elem_class in ["katex", "katex-display"]:
            return get_katex_node(elem)
        if elem_class == "user-group-mention":
            return get_user_group_mention_node(elem, silent=False)
        if elem_class == "user-group-mention silent":
            return get_user_group_mention_node(elem, silent=True)
        if elem_class == "user-mention":
            return get_user_mention_node(elem, silent=False)
        if elem_class == "user-mention silent":
            return get_user_mention_node(elem, silent=True)

        raise AssertionError("unexpected class for span")

    if elem.tag == "strong":
        restrict_attributes(elem)
        return StrongNode(children=get_child_nodes(elem))

    if elem.tag == "table":
        return get_table_node(elem)

    if elem.tag == "time":
        return get_time_widget_node(elem)

    if elem.tag == "ul":
        return get_unordered_list_node(elem)

    raise Exception(f"Unsupported tag {elem.tag}")


def get_node(elem: Element) -> BaseNode:
    node = _get_node(elem)

    expected_html = get_html(elem)

    if str(node.as_html()) != expected_html:
        print("\n------- as_html MISMATCH\n")
        print(repr(expected_html))
        print()
        print(repr(str(node.as_html())))
        print()
        raise AssertionError("as_html is not precise")

    return node


def get_message_node(html: str) -> BaseNode:
    root = etree.HTML("<body>" + html + "</body>")
    assert root.tag == "html"
    assert len(root) == 1
    body = root[0]
    assert body.tag == "body"
    message_node = get_node(body)
    return message_node
