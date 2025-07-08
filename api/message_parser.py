from typing import Callable, Union

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


class IllegalMessage(Exception):
    pass


def ensure_attribute(elem: Element, field: str, expected: str) -> None:
    ensure_equal(get_string(elem, field), expected)


def ensure_class(elem: Element, expected: str) -> None:
    ensure_equal(get_string(elem, "class"), expected)


def ensure_contains_text(elem: Element, expected: str) -> None:
    ensure_equal(elem.text or "", expected)
    if len(elem) != 0:
        print(etree.tostring(elem, with_tail=False))
        raise IllegalMessage(f"{elem.tag} has unexpected non-text children")


def ensure_empty(elem: Element) -> None:
    if elem.text or len(elem) > 0:
        raise IllegalMessage(f"{elem} is not empty")


def ensure_equal(s1: str, s2: str) -> None:
    if s1 != s2:
        print(repr(s1))
        print(repr(s2))
        raise IllegalMessage(f"{s1} != {s2}")


def ensure_newline(s: str | None) -> None:
    if s != "\n":
        raise IllegalMessage("expected newline for pretty HTML")


def ensure_num_children(elem: Element, count: int) -> None:
    if len(elem) != count:
        raise IllegalMessage("bad count")


def ensure_tag(elem: Element, tag: str) -> None:
    ensure_equal(elem.tag, tag)


def ensure_only_text(elem: Element) -> str:
    if len(elem) != 0:
        raise IllegalMessage(f"{elem.tag} has unexpected children")
    if elem.text is None:
        raise IllegalMessage("text is missing")
    return elem.text


def forbid_children(elem: Element) -> None:
    if elem.text:
        raise IllegalMessage("unexpected text")
    if len(elem) != 0:
        raise IllegalMessage(f"{elem.tag} has unexpected children")


def get_bool(elem: Element, field: str) -> bool:
    val = elem.get(field)
    if val is None:
        return False
    return val == "true"


def get_class(elem: Element, *expected: str) -> str:
    tag_class = get_string(elem, "class")
    if tag_class not in expected:
        raise IllegalMessage(f"unknown class {tag_class}")
    return tag_class


def get_html(elem: Element) -> str:
    return etree.tostring(elem, with_tail=False).decode("utf-8")


def get_database_id(elem: Element, field: str) -> int:
    s = get_string(elem, field)
    try:
        return int(s)
    except ValueError:
        raise IllegalMessage("not valid int")


def get_only_child(elem: Element, tag_name: str) -> Element:
    ensure_num_children(elem, 1)
    if elem.text is not None:
        raise IllegalMessage("unexpected text")
    child = elem[0]
    if child.tail is not None:
        raise IllegalMessage("unexpected tail")
    ensure_equal(child.tag, tag_name)
    return child


def get_only_block_child(elem: Element, tag_name: str) -> Element:
    ensure_num_children(elem, 1)
    ensure_newline(elem.text)
    child = elem[0]
    ensure_newline(child.tail)
    ensure_equal(child.tag, tag_name)
    return child


def get_optional_int(elem: Element, field: str) -> int | None:
    val = maybe_get_string(elem, field)
    if val is None:
        return None
    return int(val)


def get_string(elem: Element, field: str, allow_empty: bool = False) -> str:
    s = maybe_get_string(elem, field)
    if s is None:
        raise IllegalMessage(f"{field} is missing")
    if s == "" and not allow_empty:
        raise IllegalMessage(f"{field} is empty string")
    return s


def get_two_children(elem: Element) -> tuple[Element, Element]:
    ensure_num_children(elem, 2)
    if elem.text is not None:
        raise IllegalMessage("unexpected text")
    for c in elem:
        if c.tail is not None:
            raise IllegalMessage("unexpected tail")
    return elem[0], elem[1]


def get_two_block_children(elem: Element) -> tuple[Element, Element]:
    ensure_num_children(elem, 2)
    ensure_newline(elem.text)
    for c in elem:
        ensure_newline(c.tail)
    return elem[0], elem[1]


def maybe_get_string(elem: Element, field: str) -> str | None:
    return elem.get(field)


def restrict(elem: Element, tag: str, *fields: str) -> None:
    ensure_equal(elem.tag or "", tag)
    restrict_attributes(elem, *fields)


def restrict_attributes(elem: Element, *fields: str) -> None:
    if not set(elem.attrib).issubset(set(fields)):
        print(etree.tostring(elem, with_tail=False))
        raise IllegalMessage(
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
    lang = maybe_get_string(elem, "data-code-language")
    content = text_content(elem)
    return PygmentsCodeBlockNode(html=SafeHtml.trust(html), lang=lang, content=content)


def get_emoji_image_node(elem: Element) -> EmojiImageNode:
    restrict(elem, "img", "alt", "class", "src", "title")
    alt = get_string(elem, "alt")
    src = get_string(elem, "src")
    title = get_string(elem, "title")
    ensure_equal(alt, f":{title.replace(' ', '_')}:")
    return EmojiImageNode(src=src, title=title)


def get_emoji_span_node(elem: Element) -> EmojiSpanNode:
    restrict(elem, "span", "aria-label", "class", "role", "title")
    title = get_string(elem, "title")
    ensure_attribute(elem, "role", "img")
    ensure_attribute(elem, "aria-label", title)
    elem_class = get_string(elem, "class")
    if not elem_class.startswith("emoji "):
        raise IllegalMessage("bad class for emoji span")
    _, emoji_unicode_class = elem_class.split(" ")
    emoji_prefix, *unicodes = emoji_unicode_class.split("-")
    ensure_equal(emoji_prefix, "emoji")
    if not unicodes:
        raise IllegalMessage("bad unicode values in class for emoji")
    ensure_contains_text(elem, f":{title.replace(' ', '_')}:")
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
    original_dimensions = maybe_get_string(elem, "data-original-dimensions")
    original_content_type = maybe_get_string(elem, "data-original-content-type")
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
    ensure_class(elem, "message_inline_image")
    anchor = get_only_child(elem, "a")
    restrict(anchor, "a", "href", "title")
    href = get_string(anchor, "href")
    title = maybe_get_string(anchor, "title")
    img = get_only_child(anchor, "img")

    return InlineImageNode(
        img=get_img_node(img),
        href=href,
        title=title,
    )


def get_inline_video_node(elem: Element) -> InlineVideoNode:
    restrict(elem, "div", "class")
    ensure_class(elem, "message_inline_image message_inline_video")

    anchor = get_only_child(elem, "a")

    restrict(anchor, "a", "href", "title")
    href = get_string(anchor, "href")
    title = maybe_get_string(anchor, "title")

    video = get_only_child(anchor, "video")

    restrict(video, "video", "preload", "src")
    ensure_attribute(video, "preload", "metadata")
    src = get_string(video, "src")
    ensure_empty(video)

    return InlineVideoNode(href=href, src=src, title=title)


def get_list_item_node(elem: Element) -> ListItemNode:
    restrict(elem, "li")
    return ListItemNode(children=get_child_nodes(elem))


def get_list_item_nodes(elem: Element) -> list[ListItemNode]:
    children: list[ListItemNode] = []
    ensure_newline(elem.text)

    for c in elem:
        ensure_newline(c.tail)
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
    ensure_class(elem, "spoiler-content")
    ensure_attribute(elem, "aria-hidden", "true")
    aria_attribute_comes_first = list(elem.attrib.keys())[0] == "aria-hidden"
    return SpoilerContentNode(
        children=get_child_nodes(elem, ignore_newlines=True),
        aria_attribute_comes_first=aria_attribute_comes_first,
    )


def get_spoiler_header(elem: Element) -> SpoilerHeaderNode:
    restrict(elem, "div", "class")
    ensure_class(elem, "spoiler-header")
    return SpoilerHeaderNode(children=get_child_nodes(elem, ignore_newlines=True))


def get_spoiler_node(elem: Element) -> SpoilerNode:
    restrict(elem, "div", "class")
    ensure_class(elem, "spoiler-block")
    header_elem, content_elem = get_two_children(elem)
    header = get_spoiler_header(header_elem)
    content = get_spoiler_content(content_elem)
    return SpoilerNode(header=header, content=content)


def get_stream_link_node(elem: Element, *, has_topic: bool) -> StreamLinkNode:
    restrict(elem, "a", "class", "data-stream-id", "href")
    stream_id = get_database_id(elem, "data-stream-id")
    href = get_string(elem, "href")
    children = get_child_nodes(elem)
    return StreamLinkNode(
        href=href, stream_id=stream_id, children=children, has_topic=has_topic
    )


def get_table_cell_alignment(elem: Element) -> str | None:
    restrict_attributes(elem, "style")
    style = maybe_get_string(elem, "style")
    if style is None:
        return None
    label, value = style.strip(";").split(": ")
    ensure_equal(label, "text-align")
    if value not in ("center", "left", "right"):
        raise IllegalMessage("bad alignment value")
    return value


def get_table_node(elem: Element) -> TableNode:
    def get_thead_node(thead: Element) -> THeadNode:
        def get_th_node(th: Element) -> ThNode:
            text_align = get_table_cell_alignment(th)
            children = get_child_nodes(th)
            return ThNode(text_align=text_align, children=children)

        tr = get_only_block_child(thead, "tr")
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

    thead_elem, tbody_elem = get_two_block_children(elem)
    thead = get_thead_node(thead_elem)
    tbody = get_tbody_node(tbody_elem)
    return TableNode(thead=thead, tbody=tbody)


def get_time_widget_node(elem: Element) -> TimeWidgetNode:
    restrict(elem, "time", "datetime")
    datetime = get_string(elem, "datetime")
    text = ensure_only_text(elem)
    return TimeWidgetNode(datetime=datetime, text=text)


def get_unordered_list_node(elem: Element) -> UnorderedListNode:
    restrict_attributes(elem)
    children = get_list_item_nodes(elem)
    return UnorderedListNode(children=children)


def get_user_group_mention_node(elem: Element, silent: bool) -> UserGroupMentionNode:
    restrict(elem, "span", "class", "data-user-group-id")
    name = ensure_only_text(elem)
    group_id = get_database_id(elem, "data-user-group-id")
    return UserGroupMentionNode(name=name, group_id=group_id, silent=silent)


def get_user_mention_node(elem: Element, silent: bool) -> UserMentionNode:
    restrict(elem, "span", "class", "data-user-id")
    name = ensure_only_text(elem)
    user_id = get_database_id(elem, "data-user-id")
    return UserMentionNode(name=name, user_id=user_id, silent=silent)


"""
Now glue it all together.
"""


def verify_round_trip(
    f: Callable[[Element], BaseNode],
) -> Callable[[Element], BaseNode]:
    def new_f(elem: Element) -> BaseNode:
        node = f(elem)

        expected_html = get_html(elem)

        if str(node.as_html()) != expected_html:
            print("\n------- as_html MISMATCH\n")
            print(repr(expected_html))
            print()
            print(repr(str(node.as_html())))
            print()
            raise IllegalMessage("as_html does not round trip")

        return node

    return new_f


TextFormattingNode = Union[
    CodeNode, DeleteNode, EmphasisNode, StrongNode, TimeWidgetNode
]


def get_text_formatting_node(elem: Element) -> TextFormattingNode:
    if elem.tag == "code":
        restrict_attributes(elem)
        return CodeNode(children=get_child_nodes(elem))

    if elem.tag == "del":
        restrict_attributes(elem)
        return DeleteNode(children=get_child_nodes(elem))

    if elem.tag == "em":
        restrict_attributes(elem)
        return EmphasisNode(children=get_child_nodes(elem))

    if elem.tag == "strong":
        restrict_attributes(elem)
        return StrongNode(children=get_child_nodes(elem))

    if elem.tag == "time":
        return get_time_widget_node(elem)

    raise IllegalMessage("not a text node")


LinkNode = Union[AnchorNode, EmojiImageNode, MessageLinkNode, StreamLinkNode]


def get_link_node(elem: Element) -> LinkNode:
    elem_class = maybe_get_string(elem, "class")

    if elem.tag == "a":
        if elem_class == "message-link":
            return get_message_link_node(elem)

        if elem_class == "stream":
            return get_stream_link_node(elem, has_topic=False)

        if elem_class == "stream-topic":
            return get_stream_link_node(elem, has_topic=True)

        restrict_attributes(elem, "href")
        href = get_string(elem, "href", allow_empty=True)
        return AnchorNode(href=href, children=get_child_nodes(elem))

    if elem.tag == "img":
        if elem_class == "emoji":
            return get_emoji_image_node(elem)
        raise IllegalMessage("unexpected img tag")

    raise IllegalMessage("not a link node")


SpanNode = Union[EmojiSpanNode, KatexNode, UserGroupMentionNode, UserMentionNode]


def get_span_node(elem: Element) -> SpanNode:
    elem_class = maybe_get_string(elem, "class")

    if elem_class is None:
        raise IllegalMessage("span tags need a class")

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

    raise IllegalMessage("unexpected span tag")


PhrasingNode = Union[BreakNode, TextFormattingNode, LinkNode, SpanNode]


def maybe_get_phrasing_node(elem: Element) -> PhrasingNode | None:
    if elem.tag in ["code", "del", "em", "strong", "time"]:
        return get_text_formatting_node(elem)

    if elem.tag in ["a", "img"]:
        return get_link_node(elem)

    if elem.tag == "br":
        restrict_attributes(elem)
        forbid_children(elem)
        return BreakNode()

    if elem.tag == "span":
        return get_span_node(elem)

    return None


def get_child_nodes(elem: Element, ignore_newlines: bool = False) -> list[BaseNode]:
    children: list[BaseNode] = []
    if elem.text:
        text = elem.text
        if text and not (ignore_newlines and text == "\n"):
            children.append(TextNode(value=text))

    for c in elem:
        children.append(get_node(c))
        tail_text = c.tail or ""
        if tail_text and not (ignore_newlines and tail_text == "\n"):
            children.append(TextNode(value=tail_text))

    return children


@verify_round_trip
def get_node(elem: Element) -> BaseNode:
    elem_class = maybe_get_string(elem, "class")

    node = maybe_get_phrasing_node(elem)
    if node is not None:
        return node

    if elem.tag == "blockquote":
        restrict_attributes(elem)
        return BlockQuoteNode(children=get_child_nodes(elem))

    if elem.tag == "body":
        restrict_attributes(elem)
        return BodyNode(children=get_child_nodes(elem))

    if elem.tag == "div":
        if elem_class == "codehilite":
            return get_code_block_node(elem)
        if elem_class == "spoiler-block":
            return get_spoiler_node(elem)
        if elem_class == "message_inline_image":
            return get_inline_image_node(elem)
        if elem_class == "message_inline_image message_inline_video":
            return get_inline_video_node(elem)

        raise IllegalMessage("unexpected div tag")

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

    if elem.tag == "ol":
        return get_ordered_list_node(elem)

    if elem.tag == "p":
        restrict_attributes(elem)
        return ParagraphNode(children=get_child_nodes(elem))

    if elem.tag == "table":
        return get_table_node(elem)

    if elem.tag == "ul":
        return get_unordered_list_node(elem)

    raise IllegalMessage(f"Unsupported tag {elem.tag}")


def get_message_node(html: str) -> BaseNode:
    root = etree.HTML("<body>" + html + "</body>")
    restrict(root, "html")
    body = get_only_child(root, "body")
    restrict(body, "body")
    message_node = get_node(body)
    return message_node
