from dataclasses import dataclass
from typing import Callable

from html_helpers import SafeHtml
from lxml import etree
from message_node import (
    AnchorNode,
    BaseNode,
    BlockQuoteNode,
    BodyNode,
    BreakNode,
    ChannelWildcardMentionNode,
    ChannelWildcardMentionSilentNode,
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
    LinkNode,
    ListItemNode,
    MentionNode,
    MessageLinkNode,
    OrderedListNode,
    ParagraphNode,
    PhrasingNode,
    PygmentsCodeBlockNode,
    SpanNode,
    SpoilerContentNode,
    SpoilerHeaderNode,
    SpoilerNode,
    StreamLinkNode,
    StrongNode,
    TableNode,
    TBodyNode,
    TdNode,
    TexErrorNode,
    TextFormattingNode,
    TextNode,
    THeadNode,
    ThematicBreakNode,
    ThNode,
    TimeStampErrorNode,
    TimeWidgetNode,
    TopicMentionNode,
    TopicMentionSilentNode,
    TrNode,
    UnorderedListNode,
    UserGroupMentionNode,
    UserGroupMentionSilentNode,
    UserMentionNode,
    UserMentionSilentNode,
    ListNode,
    LoudMentionNode,
    SilentMentionNode,
)


class Element:
    pass


@dataclass
class TextElement(Element):
    text: str


@dataclass
class TagElement(Element):
    html: str
    tag: str
    attrib: dict[str, str]
    children: list["Element"]

    def get(self, field: str) -> str | None:
        return self.attrib.get(field)

    @staticmethod
    def from_lxml(elem: etree._Element) -> "TagElement":
        children: list["Element"] = []

        if elem.text is not None:
            children.append(TextElement(text=elem.text))

        for c in elem.iterchildren():
            children.append(TagElement.from_lxml(c))

            if c.tail is not None:
                children.append(TextElement(text=c.tail))

        return TagElement(
            html=etree.tostring(elem, with_tail=False).decode("utf-8"),
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


def get_html(elem: TagElement) -> str:
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


"""
Custom validators follow.
"""


def get_channel_wildcard_mention_node(elem: TagElement) -> ChannelWildcardMentionNode:
    restrict(elem, "span", "class", "data-user-id")
    name = ensure_only_text(elem)
    ensure_class(elem, "user-mention channel-wildcard-mention")
    ensure_attribute(elem, "data-user-id", "*")

    # Fight mypy being dumb about literals.
    if name == "@all":
        return ChannelWildcardMentionNode(name="@all")
    if name == "@channel":
        return ChannelWildcardMentionNode(name="@channel")
    if name == "@everyone":
        return ChannelWildcardMentionNode(name="@everyone")
    raise IllegalMessage("bad mention")


def get_channel_wildcard_mention_silent_node(
    elem: TagElement,
) -> ChannelWildcardMentionSilentNode:
    restrict(elem, "span", "class", "data-user-id")
    name = ensure_only_text(elem)
    ensure_class(elem, "user-mention channel-wildcard-mention silent")
    ensure_attribute(elem, "data-user-id", "*")

    # Fight mypy being dumb about literals.
    if name == "all":
        return ChannelWildcardMentionSilentNode(name="all")
    if name == "channel":
        return ChannelWildcardMentionSilentNode(name="channel")
    if name == "everyone":
        return ChannelWildcardMentionSilentNode(name="everyone")
    raise IllegalMessage("bad mention")


def get_code_block_node(elem: TagElement) -> PygmentsCodeBlockNode:
    restrict(elem, "div", "class", "data-code-language")
    html = get_html(elem)
    lang = maybe_get_string(elem, "data-code-language")
    content = text_content(elem)
    return PygmentsCodeBlockNode(html=SafeHtml.trust(html), lang=lang, content=content)


def get_emoji_image_node(elem: TagElement) -> EmojiImageNode:
    restrict(elem, "img", "alt", "class", "src", "title")
    alt = get_string(elem, "alt")
    src = get_string(elem, "src")
    title = get_string(elem, "title")
    ensure_equal(alt, f":{title.replace(' ', '_')}:")
    return EmojiImageNode(src=src, title=title)


def get_emoji_span_node(elem: TagElement) -> EmojiSpanNode:
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


def get_img_node(elem: TagElement) -> InlineImageChildImgNode:
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


def get_katex_node(elem: TagElement) -> KatexNode:
    restrict(elem, "span", "class")
    tag_class = get_class(elem, "katex", "katex-display")
    html = get_html(elem)
    return KatexNode(html=SafeHtml.trust(html), tag_class=tag_class)


def get_inline_image_node(elem: TagElement) -> InlineImageNode:
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


def get_inline_video_node(elem: TagElement) -> InlineVideoNode:
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


def get_list_item_node(elem: TagElement) -> ListItemNode:
    restrict(elem, "li")
    return ListItemNode(children=get_child_nodes(elem))


def get_list_item_nodes(elem: TagElement) -> list[ListItemNode]:
    children: list[ListItemNode] = []

    for c in elem.children:
        if isinstance(c, TextElement):
            ensure_newline(c)
        elif isinstance(c, TagElement):
            children.append(get_list_item_node(c))

    return children


def get_ordered_list_node(elem: TagElement) -> OrderedListNode:
    restrict(elem, "ol", "start")
    start = get_optional_int(elem, "start")
    children = get_list_item_nodes(elem)
    return OrderedListNode(children=children, start=start)


def get_message_link_node(elem: TagElement) -> MessageLinkNode:
    restrict(elem, "a", "class", "href")
    href = get_string(elem, "href")
    children = get_phrasing_nodes(elem)
    return MessageLinkNode(
        href=href,
        children=children,
    )


def get_spoiler_content(elem: TagElement) -> SpoilerContentNode:
    restrict(elem, "div", "class", "aria-hidden")
    ensure_class(elem, "spoiler-content")
    ensure_attribute(elem, "aria-hidden", "true")
    aria_attribute_comes_first = list(elem.attrib.keys())[0] == "aria-hidden"
    return SpoilerContentNode(
        children=get_child_nodes(elem),
        aria_attribute_comes_first=aria_attribute_comes_first,
    )


def get_spoiler_header(elem: TagElement) -> SpoilerHeaderNode:
    restrict(elem, "div", "class")
    ensure_class(elem, "spoiler-header")
    return SpoilerHeaderNode(children=get_child_nodes(elem, ignore_newlines=True))


def get_spoiler_node(elem: TagElement) -> SpoilerNode:
    restrict(elem, "div", "class")
    ensure_class(elem, "spoiler-block")
    header_elem, content_elem = get_two_children(elem)
    header = get_spoiler_header(header_elem)
    content = get_spoiler_content(content_elem)
    return SpoilerNode(header=header, content=content)


def get_stream_link_node(elem: TagElement, *, has_topic: bool) -> StreamLinkNode:
    restrict(elem, "a", "class", "data-stream-id", "href")
    stream_id = get_database_id(elem, "data-stream-id")
    href = get_string(elem, "href")
    children = get_phrasing_nodes(elem)
    return StreamLinkNode(
        href=href, stream_id=stream_id, children=children, has_topic=has_topic
    )


def get_table_cell_alignment(elem: TagElement) -> str | None:
    restrict_attributes(elem, "style")
    style = maybe_get_string(elem, "style")
    if style is None:
        return None
    label, value = style.strip(";").split(": ")
    ensure_equal(label, "text-align")
    if value not in ("center", "left", "right"):
        raise IllegalMessage("bad alignment value")
    return value


def get_table_node(elem: TagElement) -> TableNode:
    def get_thead_node(thead: TagElement) -> THeadNode:
        def get_th_node(th: TagElement) -> ThNode:
            text_align = get_table_cell_alignment(th)
            children = get_child_nodes(th)
            return ThNode(text_align=text_align, children=children)

        tr = get_only_block_child(thead, "tr")
        ths = [get_th_node(th) for th in get_tag_children(tr)]
        return THeadNode(ths=ths)

    def get_tbody_node(tbody: TagElement) -> TBodyNode:
        def get_tr_node(tr: TagElement) -> TrNode:
            def get_td_node(td: TagElement) -> TdNode:
                text_align = get_table_cell_alignment(td)
                children = get_child_nodes(td)
                return TdNode(text_align=text_align, children=children)

            tds = [get_td_node(td) for td in get_tag_children(tr)]
            return TrNode(tds=tds)

        trs = [get_tr_node(tr) for tr in get_tag_children(tbody)]
        return TBodyNode(trs=trs)

    thead_elem, tbody_elem = get_two_block_children(elem)
    thead = get_thead_node(thead_elem)
    tbody = get_tbody_node(tbody_elem)
    return TableNode(thead=thead, tbody=tbody)


def get_tex_error_node(elem: TagElement) -> TexErrorNode:
    restrict(elem, "span", "class")
    ensure_class(elem, "tex-error")
    text = ensure_only_text(elem)
    return TexErrorNode(text=text)


def get_time_widget_node(elem: TagElement) -> TimeWidgetNode:
    restrict(elem, "time", "datetime")
    datetime = get_string(elem, "datetime")
    text = ensure_only_text(elem)
    return TimeWidgetNode(datetime=datetime, text=text)


def get_timestamp_error_node(elem: TagElement) -> TimeStampErrorNode:
    restrict(elem, "span", "class")
    ensure_class(elem, "timestamp-error")
    text = ensure_only_text(elem)
    return TimeStampErrorNode(text=text)


def get_topic_mention_node(elem: TagElement) -> TopicMentionNode:
    restrict(elem, "span", "class")
    name = ensure_only_text(elem)
    if name != "@topic":
        raise IllegalMessage("bad wildcard mention")
    ensure_class(elem, "topic-mention")
    return TopicMentionNode()


def get_topic_mention_silent_node(elem: TagElement) -> TopicMentionSilentNode:
    restrict(elem, "span", "class")
    name = ensure_only_text(elem)
    if name != "topic":
        raise IllegalMessage("bad wildcard mention")
    ensure_class(elem, "topic-mention silent")
    return TopicMentionSilentNode()


def get_unordered_list_node(elem: TagElement) -> UnorderedListNode:
    restrict_attributes(elem)
    children = get_list_item_nodes(elem)
    return UnorderedListNode(children=children)


def get_user_group_mention_node(elem: TagElement) -> UserGroupMentionNode:
    restrict(elem, "span", "class", "data-user-group-id")
    ensure_class(elem, "user-group-mention")
    name = ensure_only_text(elem)
    group_id = get_database_id(elem, "data-user-group-id")
    return UserGroupMentionNode(name=name, group_id=group_id)


def get_user_group_mention_silent_node(elem: TagElement) -> UserGroupMentionSilentNode:
    restrict(elem, "span", "class", "data-user-group-id")
    ensure_class(elem, "user-group-mention silent")
    name = ensure_only_text(elem)
    group_id = get_database_id(elem, "data-user-group-id")
    return UserGroupMentionSilentNode(name=name, group_id=group_id)


def get_user_mention_node(elem: TagElement) -> UserMentionNode:
    restrict(elem, "span", "class", "data-user-id")
    ensure_class(elem, "user-mention")
    name = ensure_only_text(elem)
    user_id = get_database_id(elem, "data-user-id")
    return UserMentionNode(name=name, user_id=user_id)


def get_user_mention_silent_node(elem: TagElement) -> UserMentionSilentNode:
    restrict(elem, "span", "class", "data-user-id")
    ensure_class(elem, "user-mention silent")
    name = ensure_only_text(elem)
    user_id = get_database_id(elem, "data-user-id")
    return UserMentionSilentNode(name=name, user_id=user_id)


"""
Now glue it all together.
"""


def verify_round_trip(
    f: Callable[[TagElement], BaseNode],
) -> Callable[[TagElement], BaseNode]:
    def new_f(elem: TagElement) -> BaseNode:
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


def get_text_formatting_node(elem: TagElement) -> TextFormattingNode:
    if elem.tag == "del":
        restrict_attributes(elem)
        return DeleteNode(children=get_phrasing_nodes(elem))

    if elem.tag == "em":
        restrict_attributes(elem)
        return EmphasisNode(children=get_phrasing_nodes(elem))

    if elem.tag == "strong":
        restrict_attributes(elem)
        return StrongNode(children=get_phrasing_nodes(elem))

    raise IllegalMessage("not a text node")


def get_link_node(elem: TagElement) -> LinkNode:
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
        return AnchorNode(href=href, children=get_phrasing_nodes(elem))

    if elem.tag == "img":
        if elem_class == "emoji":
            return get_emoji_image_node(elem)
        raise IllegalMessage("unexpected img tag")

    raise IllegalMessage("not a link node")


def get_loud_mention_node(elem: TagElement) -> LoudMentionNode | None:
    elem_class = get_string(elem, "class")

    if elem_class == "topic-mention":
        return get_topic_mention_node(elem)
    if elem_class == "user-group-mention":
        return get_user_group_mention_node(elem)
    if elem_class == "user-mention channel-wildcard-mention":
        return get_channel_wildcard_mention_node(elem)
    if elem_class == "user-mention":
        return get_user_mention_node(elem)

    return None


def get_silent_mention_node(elem: TagElement) -> SilentMentionNode | None:
    elem_class = get_string(elem, "class")

    if elem_class == "topic-mention silent":
        return get_topic_mention_silent_node(elem)
    if elem_class == "user-group-mention silent":
        return get_user_group_mention_silent_node(elem)
    if elem_class == "user-mention channel-wildcard-mention silent":
        return get_channel_wildcard_mention_silent_node(elem)
    if elem_class == "user-mention silent":
        return get_user_mention_silent_node(elem)

    return None


def get_mention_node(elem: TagElement) -> MentionNode | None:
    loud = get_loud_mention_node(elem)
    if loud is not None:
        return loud

    silent = get_silent_mention_node(elem)
    if silent is not None:
        return silent

    return None


def get_span_node(elem: TagElement) -> SpanNode:
    elem_class = maybe_get_string(elem, "class")

    if elem_class is None:
        raise IllegalMessage("span tags need a class")

    if elem_class.startswith("emoji "):
        return get_emoji_span_node(elem)
    if elem_class in ["katex", "katex-display"]:
        return get_katex_node(elem)
    if elem_class == "tex-error":
        return get_tex_error_node(elem)
    if elem_class == "timestamp-error":
        return get_timestamp_error_node(elem)

    maybe_mention_node = get_mention_node(elem)
    if maybe_mention_node is not None:
        return maybe_mention_node

    raise IllegalMessage("unexpected span tag")


def maybe_get_phrasing_node(elem: Element) -> PhrasingNode | None:
    if isinstance(elem, TextElement):
        return TextNode(value=elem.text)

    if isinstance(elem, TagElement):
        if elem.tag in ["del", "em", "strong"]:
            return get_text_formatting_node(elem)

        if elem.tag in ["a", "img"]:
            return get_link_node(elem)

        if elem.tag == "br":
            restrict_attributes(elem)
            forbid_children(elem)
            return BreakNode()

        if elem.tag == "code":
            restrict_attributes(elem)
            return CodeNode(children=get_child_nodes(elem))

        if elem.tag == "span":
            return get_span_node(elem)

        if elem.tag == "time":
            return get_time_widget_node(elem)

    return None


def get_child_nodes(elem: TagElement, ignore_newlines: bool = False) -> list[BaseNode]:
    children: list[BaseNode] = []

    for c in elem.children:
        if isinstance(c, TextElement):
            if ignore_newlines:
                ensure_newline(c)
            else:
                children.append(TextNode(value=c.text))
        elif isinstance(c, TagElement):
            children.append(get_node(c))
    return children


def get_list_node(elem: TagElement) -> ListNode:
    if elem.tag == "ol":
        return get_ordered_list_node(elem)

    if elem.tag == "ul":
        return get_unordered_list_node(elem)

    raise IllegalMessage(f"Unsupported tag {elem.tag}")


def get_phrasing_nodes(elem: TagElement) -> list[PhrasingNode]:
    children: list[PhrasingNode] = []

    for c in elem.children:
        child_node = maybe_get_phrasing_node(c)
        if child_node is None:
            raise IllegalMessage("expected phrasing node")
        children.append(child_node)

    return children


@verify_round_trip
def get_node(elem: TagElement) -> BaseNode:
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
        return HeadingNode(depth=1, children=get_phrasing_nodes(elem))

    if elem.tag == "h2":
        return HeadingNode(depth=2, children=get_phrasing_nodes(elem))

    if elem.tag == "h3":
        return HeadingNode(depth=3, children=get_phrasing_nodes(elem))

    if elem.tag == "h4":
        return HeadingNode(depth=4, children=get_phrasing_nodes(elem))

    if elem.tag == "h5":
        return HeadingNode(depth=5, children=get_phrasing_nodes(elem))

    if elem.tag == "h6":
        return HeadingNode(depth=6, children=get_phrasing_nodes(elem))

    if elem.tag == "hr":
        restrict_attributes(elem)
        forbid_children(elem)
        return ThematicBreakNode()

    if elem.tag in ["ol", "ul"]:
        return get_list_node(elem)

    if elem.tag == "p":
        restrict_attributes(elem)
        return ParagraphNode(children=get_child_nodes(elem))

    if elem.tag == "table":
        return get_table_node(elem)

    raise IllegalMessage(f"Unsupported tag {elem.tag}")


def get_message_node(html: str) -> BaseNode:
    # We try to be strict, but lxml doesn't like math/video/time and doesn't
    # recover from certain <br> tags in paragraphs.
    if (
        "<math" in html
        or "<video" in html
        or "<time" in html
        or "<br" in html
        or "</a></a>" in html
    ):
        recover = True
    else:
        recover = False
    parser = etree.HTMLParser(recover=recover)
    lxml_root = etree.fromstring("<body>" + html + "</body>", parser=parser)
    root = TagElement.from_lxml(lxml_root)
    restrict(root, "html")
    body = get_only_child(root, "body")
    restrict(body, "body")
    message_node = get_node(body)
    return message_node
