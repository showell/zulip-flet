from abc import ABC, abstractmethod
from typing import Callable, Literal, Optional, Sequence

from html_element import (
    Element,
    IllegalMessage,
    TagElement,
    TextElement,
    ensure_attribute,
    ensure_class,
    ensure_contains_text,
    ensure_empty,
    ensure_equal,
    ensure_newline,
    ensure_only_text,
    forbid_children,
    get_bool,
    get_class,
    get_database_id,
    get_html,
    get_only_block_child,
    get_only_child,
    get_optional_int,
    get_string,
    get_tag_children,
    get_two_block_children,
    get_two_children,
    maybe_get_string,
    restrict,
    restrict_attributes,
    text_content,
)
from html_helpers import SafeHtml, build_tag, escape_text
from pydantic import BaseModel, Field

"""
Our BaseNode class is abstract.
"""


class BaseNode(BaseModel, ABC):
    @abstractmethod
    def as_text(self) -> str:
        pass

    @abstractmethod
    def as_html(self) -> SafeHtml:
        pass


class PhrasingNode(BaseNode, ABC):
    @staticmethod
    def maybe_get_from_element(elem: Element) -> Optional["PhrasingNode"]:
        if isinstance(elem, TextElement):
            return TextNode(value=elem.text)

        if isinstance(elem, TagElement):
            if elem.tag in ["del", "em", "strong"]:
                return TextFormattingNode.from_tag_element(elem)

            if elem.tag in ["a", "img"]:
                return LinkNode.from_tag_element(elem)

            if elem.tag == "br":
                return BreakNode.from_tag_element(elem)

            if elem.tag == "code":
                return CodeNode.from_tag_element(elem)

            if elem.tag == "span":
                return SpanNode.from_tag_element(elem)

            if elem.tag == "time":
                return TimeWidgetNode.from_tag_element(elem)

        return None

    @staticmethod
    def get_child_nodes(elem: TagElement) -> list["PhrasingNode"]:
        children: list[PhrasingNode] = []

        for c in elem.children:
            child_node = PhrasingNode.maybe_get_from_element(c)
            if child_node is None:
                raise IllegalMessage("expected phrasing node")
            children.append(child_node)

        return children


class DivNode(BaseNode, ABC):
    @staticmethod
    def from_tag_element(elem: TagElement) -> "DivNode":
        elem_class = maybe_get_string(elem, "class")

        if elem.tag == "div":
            if elem_class == "codehilite":
                return PygmentsCodeBlockNode.from_tag_element(elem)
            if elem_class == "spoiler-block":
                return SpoilerNode.from_tag_element(elem)
            if elem_class == "message_inline_image":
                return InlineImageNode.from_tag_element(elem)
            if elem_class == "message_inline_image message_inline_video":
                return InlineVideoNode.from_tag_element(elem)

            raise IllegalMessage(f"unexpected class for div tag: {elem_class}")

        raise IllegalMessage(f"unexpected tag: {elem.tag}")


class SpanNode(PhrasingNode, ABC):
    @staticmethod
    def from_tag_element(elem: TagElement) -> "SpanNode":
        if elem.tag == "span":
            elem_class = maybe_get_string(elem, "class")

            if elem_class is None:
                raise IllegalMessage("span tags need a class")

            if elem_class.startswith("emoji "):
                return EmojiSpanNode.from_tag_element(elem)
            if elem_class in ["katex", "katex-display"]:
                return KatexNode.from_tag_element(elem)
            if elem_class == "tex-error":
                return TexErrorNode.from_tag_element(elem)
            if elem_class == "timestamp-error":
                return TimeStampErrorNode.from_tag_element(elem)

            maybe_mention_node = MentionNode.maybe_from_tag_element(elem)
            if maybe_mention_node is not None:
                return maybe_mention_node

            raise IllegalMessage("unexpected span tag")

        raise IllegalMessage(f"bad tag {elem.tag} for span")


"""
Even though HTML doesn't require you to surround
text with a text node, we model it that way in our
AST.

At the HTML level, think of it like we would have
preferred
 
    <p><text>hello</text><b><text>world</text></b></p>

over

    <p>hello<b>world</b></p>

from a parsing/manipulation perspective, even though
the latter is clearly better for humans.
"""


class TextNode(PhrasingNode):
    value: str

    def as_text(self) -> str:
        return self.value

    def as_html(self) -> SafeHtml:
        return escape_text(self.value)


"""
We generally conform to mdast conventions for naming.

The <br> and <hr> tags are handled super generically by us.

    * BreakNode == <br>
    * ThematicBreakNode == <hr>
"""


class BreakNode(PhrasingNode):
    def as_text(self) -> str:
        return "\n"

    def as_html(self) -> SafeHtml:
        return SafeHtml.trust("<br/>")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "BreakNode":
        restrict(elem, "br")
        forbid_children(elem)
        return BreakNode()


class ThematicBreakNode(BaseNode):
    def as_text(self) -> str:
        return "\n\n---\n\n"

    def as_html(self) -> SafeHtml:
        return SafeHtml.trust("<hr/>")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "ThematicBreakNode":
        restrict(elem, "hr")
        forbid_children(elem)
        return ThematicBreakNode()


"""
Here we define a ContainerNode class. Essentially, containers
have arbitrary children.  Unlike some of our other ABC classes,
which are mostly around to help mypy, the ContainerNode class
is intended more for implementation reuse purposes.

Note that there are some classes in our AST that do have
children but don't inherit from ContainerNode.  This means
that they are something like tables, in which their
child nodes are way more constrained.

We eventually want more refinement here.
"""


class ContainerNode(BaseNode, ABC):
    children: Sequence[BaseNode]

    def children_text(self) -> str:
        return " ".join(c.as_text() for c in self.children)

    def as_text(self) -> str:
        return self.children_text()

    def inner(self) -> SafeHtml:
        return SafeHtml.combine([c.as_html() for c in self.children])

    def tag(self, tag: str, **attrs: str | None) -> SafeHtml:
        return build_tag(tag=tag, inner=self.inner(), **attrs)

    def block_tag(self, tag: str, **attrs: str | None) -> SafeHtml:
        inner = SafeHtml.block_join([c.as_html() for c in self.children])
        return build_tag(tag=tag, inner=inner, **attrs)


"""
HEADINGS:

Whenever practical, I try to stay roughly at the same level of
abstraction as the mdast project.

See https://github.com/syntax-tree/mdast?tab=readme-ov-file#heading
as an example.  Instead of concretely having distinct classes for
<h1>, <h2>, etc. in my AST, I use a Heading concept with depth.

I'm still on the fence about having a catch-all HeadingNode class,
though.  I think just having six concrete classes might be nice
when I start thinking about markdown parsing and stuff like that.
(But I would probably still keep a superclass, even if it's just
an ABC.)
"""


class HeadingNode(ContainerNode):
    children: Sequence[PhrasingNode]
    depth: int = Field(ge=1, le=6)

    def as_text(self) -> str:
        return f"{'#' * self.depth} {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag(f"h{self.depth}")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "HeadingNode":
        restrict_attributes(elem)

        if elem.tag == "h1":
            return HeadingNode(depth=1, children=PhrasingNode.get_child_nodes(elem))

        if elem.tag == "h2":
            return HeadingNode(depth=2, children=PhrasingNode.get_child_nodes(elem))

        if elem.tag == "h3":
            return HeadingNode(depth=3, children=PhrasingNode.get_child_nodes(elem))

        if elem.tag == "h4":
            return HeadingNode(depth=4, children=PhrasingNode.get_child_nodes(elem))

        if elem.tag == "h5":
            return HeadingNode(depth=5, children=PhrasingNode.get_child_nodes(elem))

        if elem.tag == "h6":
            return HeadingNode(depth=6, children=PhrasingNode.get_child_nodes(elem))

        raise IllegalMessage(f"Unexpected heading tag {elem.tag}")


"""
The mostly-vanilla subclasses of ContainerNode are below.

Generally it's up to the calling code to map these into some
kind of UI paradigm.  The as_text methods are basically
for debugging and convenience.  For example, if you try
to build a UI to show a Zulip message, you can fall
back to the as_text() methods and just stick the text
into a text widget until you're ready to flesh out the UI.

---

We'll start with simple markup:

    DeleteNode == strike-through == <del>foo</del> == ~~foo~~
    EmphasisNode == italicized == <em>foo</em> == *foo*
    StrongNode == bold == <strong>foo</strong> == **foo* 
"""


class TextFormattingNode(ContainerNode, PhrasingNode, ABC):
    @staticmethod
    def from_tag_element(elem: TagElement) -> "TextFormattingNode":
        if elem.tag == "del":
            return DeleteNode.from_tag_element(elem)

        if elem.tag == "em":
            return EmphasisNode.from_tag_element(elem)

        if elem.tag == "strong":
            return StrongNode.from_tag_element(elem)

        raise IllegalMessage("not a text node")


class DeleteNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"~~{self.children_text()}~~"

    def as_html(self) -> SafeHtml:
        return self.tag("del")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "DeleteNode":
        restrict(elem, "del")
        return DeleteNode(children=PhrasingNode.get_child_nodes(elem))


class EmphasisNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"*{self.children_text()}*"

    def as_html(self) -> SafeHtml:
        return self.tag("em")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "EmphasisNode":
        restrict(elem, "em")
        return EmphasisNode(children=PhrasingNode.get_child_nodes(elem))


class StrongNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"**{self.children_text()}**"

    def as_html(self) -> SafeHtml:
        return self.tag("strong")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "StrongNode":
        restrict(elem, "strong")
        return StrongNode(children=PhrasingNode.get_child_nodes(elem))


"""
We have error nodes
"""


class ParseErrorNode(PhrasingNode, ABC):
    text: str

    @abstractmethod
    def zulip_class(self) -> str:
        pass

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.text),
            class_=self.zulip_class(),
        )


class TexErrorNode(SpanNode, ParseErrorNode):
    text: str

    def as_text(self) -> str:
        return "tex error"

    def zulip_class(self) -> str:
        return "tex-error"

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TexErrorNode":
        restrict(elem, "span", "class")
        ensure_class(elem, "tex-error")
        text = ensure_only_text(elem)
        return TexErrorNode(text=text)


class TimeStampErrorNode(SpanNode, ParseErrorNode):
    text: str

    def as_text(self) -> str:
        return "timestamp error"

    def zulip_class(self) -> str:
        return "timestamp-error"

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TimeStampErrorNode":
        restrict(elem, "span", "class")
        ensure_class(elem, "timestamp-error")
        text = ensure_only_text(elem)
        return TimeStampErrorNode(text=text)


"""
And then some more basic classes follow.
"""


class BlockQuoteNode(ContainerNode):
    def as_text(self) -> str:
        content = self.children_text()
        return f"\n-----\n{content}\n-----\n"

    def as_html(self) -> SafeHtml:
        return self.tag("blockquote")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "BlockQuoteNode":
        restrict(elem, "blockquote")
        return BlockQuoteNode(children=get_child_nodes(elem))


class BodyNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.tag("body")


class CodeNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"`{self.children_text()}`"

    def as_html(self) -> SafeHtml:
        return self.tag("code")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "CodeNode":
        restrict(elem, "code")
        return CodeNode(children=get_child_nodes(elem))


class ParagraphNode(ContainerNode):
    def as_text(self) -> str:
        return self.children_text() + "\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("p")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "ParagraphNode":
        restrict(elem, "p")
        return ParagraphNode(children=get_child_nodes(elem))


"""
We use a LinkNode ABC to classify all Zulip nodes that
link to things, either within Zulip or externally.  All
of these nodes are manifested in HTML with either an
<a> tag or an <img> tag.  For custom Zulip constructs,
we always use a "class" attribute to specify the special
type of link we are representing.

In the mdast spec, they generalize the concept of a
Resource (https://github.com/syntax-tree/mdast?tab=readme-ov-file#resource),
but I stay a bit closer to HTML lingo most of the time, using
terms like "href" and "src".
"""


class LinkNode(PhrasingNode, ABC):
    @staticmethod
    def from_tag_element(elem: TagElement) -> "LinkNode":
        elem_class = maybe_get_string(elem, "class")

        if elem.tag == "a":
            if elem_class == "message-link":
                return MessageLinkNode.from_tag_element(elem)

            if elem_class == "stream":
                return StreamLinkNode.from_tag_element(elem)

            if elem_class == "stream-topic":
                return StreamTopicLinkNode.from_tag_element(elem)

            return AnchorNode.from_tag_element(elem)

        if elem.tag == "img":
            if elem_class == "emoji":
                return EmojiImageNode.from_tag_element(elem)
            raise IllegalMessage("unexpected img tag")

        raise IllegalMessage("not a link node")


"""
Nodes that are manifested with <a> tags follow here.

The custom Zulip nodes are all called out with a class.
"""


class AnchorNode(LinkNode, ContainerNode):
    href: str

    def as_text(self) -> str:
        content = "".join(c.as_text() for c in self.children)
        return f"[{content}] ({self.href})"

    def as_html(self) -> SafeHtml:
        return self.tag("a", href=self.href)

    @staticmethod
    def from_tag_element(elem: TagElement) -> "AnchorNode":
        restrict(elem, "a", "href")
        href = get_string(elem, "href", allow_empty=True)
        return AnchorNode(href=href, children=PhrasingNode.get_child_nodes(elem))


class MessageLinkNode(LinkNode, ContainerNode):
    href: str

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text} (MESSAGE LINK: {self.href})]"

    @staticmethod
    def zulip_class() -> str:
        return "message-link"

    def as_html(self) -> SafeHtml:
        href = self.href
        return self.tag("a", class_=self.zulip_class(), href=href)

    @staticmethod
    def from_tag_element(elem: TagElement) -> "MessageLinkNode":
        restrict(elem, "a", "class", "href")
        ensure_class(elem, "message-link")
        href = get_string(elem, "href")
        children = PhrasingNode.get_child_nodes(elem)
        return MessageLinkNode(
            href=href,
            children=children,
        )


class StreamLinkNode(LinkNode, ContainerNode):
    href: str
    stream_id: int

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[STREAM {text}] ({self.href}) (stream id {self.stream_id})"

    @staticmethod
    def zulip_class() -> str:
        return "stream"

    def as_html(self) -> SafeHtml:
        return self.tag(
            "a",
            class_=self.zulip_class(),
            data_stream_id=str(self.stream_id),
            href=self.href,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "StreamLinkNode":
        restrict(elem, "a", "class", "data-stream-id", "href")
        ensure_class(elem, "stream")
        stream_id = get_database_id(elem, "data-stream-id")
        href = get_string(elem, "href")
        children = PhrasingNode.get_child_nodes(elem)
        return StreamLinkNode(href=href, stream_id=stream_id, children=children)


class StreamTopicLinkNode(LinkNode, ContainerNode):
    href: str
    stream_id: int

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[STREAM/TOPIC {text}] ({self.href}) (stream id {self.stream_id})"

    @staticmethod
    def zulip_class() -> str:
        return "stream-topic"

    def as_html(self) -> SafeHtml:
        return self.tag(
            "a",
            class_=self.zulip_class(),
            data_stream_id=str(self.stream_id),
            href=self.href,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "StreamTopicLinkNode":
        restrict(elem, "a", "class", "data-stream-id", "href")
        ensure_class(elem, "stream-topic")
        stream_id = get_database_id(elem, "data-stream-id")
        href = get_string(elem, "href")
        children = PhrasingNode.get_child_nodes(elem)
        return StreamTopicLinkNode(href=href, stream_id=stream_id, children=children)


"""
Emojis are a bit of work in Zulip.

For strict validation of emojis, we probably want something out of
the scope of this project, since Zulip allows for custom emojis.
So you would probably do additional validation by walking this AST
after we've verified that things are correct syntactically from
the incoming source of data.
"""


class EmojiImageNode(LinkNode):
    src: str
    title: str

    def as_text(self) -> str:
        return f":{self.title}:"

    @staticmethod
    def zulip_class() -> str:
        return "emoji"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="img",
            inner=SafeHtml.trust(""),
            alt=f":{self.title.replace(' ', '_')}:",
            class_=self.zulip_class(),
            src=self.src,
            title=self.title,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "EmojiImageNode":
        restrict(elem, "img", "alt", "class", "src", "title")
        alt = get_string(elem, "alt")
        src = get_string(elem, "src")
        title = get_string(elem, "title")
        ensure_equal(alt, f":{title.replace(' ', '_')}:")
        return EmojiImageNode(src=src, title=title)


class EmojiSpanNode(SpanNode):
    unicode_points: Sequence[int]
    title: str

    def as_text(self) -> str:
        c = " ".join(chr(n) for n in self.unicode_points)
        return f"{c} (:{self.title})"

    def zulip_class(self) -> str:
        unicode_suffix = "-".join(f"{num:04x}" for num in self.unicode_points)
        return f"emoji emoji-{unicode_suffix}"

    def as_html(self) -> SafeHtml:
        title = self.title
        return build_tag(
            tag="span",
            inner=escape_text(f":{title.replace(' ', '_')}:"),
            aria_label=title,
            class_=self.zulip_class(),
            role="img",
            title=title,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "EmojiSpanNode":
        restrict(elem, "span", "aria-label", "class", "role", "title")
        title = get_string(elem, "title")
        ensure_attribute(elem, "role", "img")
        ensure_attribute(elem, "aria-label", title)
        elem_class = get_string(elem, "class")
        if not elem_class.startswith("emoji "):
            raise IllegalMessage("bad class for emoji span")
        _, emoji_unicode_class = elem_class.split(" ")
        emoji_prefix, *unicode_hexes = emoji_unicode_class.split("-")
        ensure_equal(emoji_prefix, "emoji")
        if not unicode_hexes:
            raise IllegalMessage("bad unicode values in class for emoji")
        unicode_points = []
        for c in unicode_hexes:
            try:
                unicode_point = int(c, 16)
                chr(unicode_point)
            except ValueError:
                raise IllegalMessage(f"bad unicode point: {c}")
            """
            Ideally we would restrict unicode values, but simple
            checks like emoji.is_emoji (from pip install emoji)
            are too restrictive.
            """
            unicode_points.append(unicode_point)
        ensure_contains_text(elem, f":{title.replace(' ', '_')}:")
        return EmojiSpanNode(title=title, unicode_points=unicode_points)


"""
Lists
"""


class ListItemNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.tag("li")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "ListItemNode":
        restrict(elem, "li")
        return ListItemNode(children=get_child_nodes(elem))


class ListNode(BaseNode, ABC):
    children: Sequence[ListItemNode]

    @staticmethod
    def from_tag_element(elem: TagElement) -> "ListNode":
        if elem.tag == "ol":
            return OrderedListNode.from_tag_element(elem)

        if elem.tag == "ul":
            return UnorderedListNode.from_tag_element(elem)

        raise IllegalMessage(f"Unsupported tag {elem.tag}")

    @staticmethod
    def get_list_item_nodes(elem: TagElement) -> list[ListItemNode]:
        children: list[ListItemNode] = []

        for c in elem.children:
            if isinstance(c, TextElement):
                ensure_newline(c)
            elif isinstance(c, TagElement):
                children.append(ListItemNode.from_tag_element(c))

        return children


class OrderedListNode(ListNode):
    start: int | None

    def as_text(self) -> str:
        return "".join(
            f"\n    {i + (self.start or 1)}. " + c.as_text()
            for i, c in enumerate(self.children)
        )

    def as_html(self) -> SafeHtml:
        start_attr: str | None = str(self.start) if self.start else None
        list_items = SafeHtml.block_join([c.as_html() for c in self.children])
        return build_tag(
            tag="ol",
            inner=list_items,
            start=start_attr,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "OrderedListNode":
        restrict(elem, "ol", "start")
        start = get_optional_int(elem, "start")
        children = ListNode.get_list_item_nodes(elem)
        return OrderedListNode(children=children, start=start)


class UnorderedListNode(ListNode):
    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)

    def as_html(self) -> SafeHtml:
        list_items = SafeHtml.block_join([c.as_html() for c in self.children])
        return build_tag(
            tag="ul",
            inner=list_items,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "UnorderedListNode":
        restrict_attributes(elem)
        children = ListNode.get_list_item_nodes(elem)
        return UnorderedListNode(children=children)


"""
Zulip tables are their own special beast.  Zulip, to my knowledge,
doesn't do anything custom with the actual conversion of Markdown
tables into HTML tables, but we need to get granular on the description
of tables, since the headers and cells of Zulip tables **can**
include custom thingies.
"""


class TextAlignment(BaseModel):
    value: Literal["center", "left", "right"] | None

    def as_style(self) -> str | None:
        if self.value is None:
            return None
        else:
            return f"text-align: {self.value};"

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TextAlignment":
        style = maybe_get_string(elem, "style")
        if style is None:
            return TextAlignment(value=None)
        label, value = style.strip(";").split(": ")
        ensure_equal(label, "text-align")
        if value == "center":
            return TextAlignment(value="center")
        if value == "left":
            return TextAlignment(value="left")
        if value == "right":
            return TextAlignment(value="right")
        raise IllegalMessage("bad alignment value")


class ThNode(ContainerNode):
    text_align: TextAlignment

    def as_text(self) -> str:
        return f"    TH: {self.children_text()} ({self.text_align.value})\n"

    def as_html(self) -> SafeHtml:
        style = self.text_align.as_style()
        return self.tag("th", style=style)

    @staticmethod
    def from_tag_element(th: TagElement) -> "ThNode":
        restrict(th, "th", "style")
        text_align = TextAlignment.from_tag_element(th)
        children = get_child_nodes(th)
        return ThNode(text_align=text_align, children=children)


class TdNode(ContainerNode):
    text_align: TextAlignment

    def as_text(self) -> str:
        return f"    TD: {self.children_text()} ({self.text_align.value})\n"

    def as_html(self) -> SafeHtml:
        style = self.text_align.as_style()
        return self.tag("td", style=style)

    @staticmethod
    def from_tag_element(td: TagElement) -> "TdNode":
        restrict(td, "td", "style")
        text_align = TextAlignment.from_tag_element(td)
        children = get_child_nodes(td)
        return TdNode(text_align=text_align, children=children)


class TrNode(BaseNode):
    tds: Sequence[TdNode]

    def as_text(self) -> str:
        s = "TR\n"
        for td in self.tds:
            s += td.as_text()
        s += "\n"
        return s

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.block_join([td.as_html() for td in self.tds])
        return build_tag(tag="tr", inner=inner)

    @staticmethod
    def from_tag_element(tr: TagElement) -> "TrNode":
        restrict(tr, "tr")
        tds = [TdNode.from_tag_element(td) for td in get_tag_children(tr)]
        return TrNode(tds=tds)


class TBodyNode(BaseNode):
    trs: Sequence[TrNode]

    def as_text(self) -> str:
        tr_text = "".join(tr.as_text() for tr in self.trs)
        return f"\n-----------\n{tr_text}"

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.block_join([tr.as_html() for tr in self.trs])
        return build_tag(tag="tbody", inner=inner)

    @staticmethod
    def from_tag_element(tbody: TagElement) -> "TBodyNode":
        restrict(tbody, "tbody")
        trs = [TrNode.from_tag_element(tr) for tr in get_tag_children(tbody)]
        return TBodyNode(trs=trs)


class THeadNode(BaseNode):
    ths: Sequence[ThNode]

    def as_text(self) -> str:
        th_text = "".join(th.as_text() for th in self.ths)
        return f"\n-----------\n{th_text}"

    def as_html(self) -> SafeHtml:
        ths = SafeHtml.block_join([th.as_html() for th in self.ths])
        tr = build_tag(tag="tr", inner=ths)
        return build_tag(tag="thead", inner=SafeHtml.block_join([tr]))

    @staticmethod
    def from_tag_element(thead: TagElement) -> "THeadNode":
        restrict(thead, "thead")
        tr = get_only_block_child(thead, "tr")
        ths = [ThNode.from_tag_element(th) for th in get_tag_children(tr)]
        return THeadNode(ths=ths)


class TableNode(BaseNode):
    thead: THeadNode
    tbody: TBodyNode

    def as_text(self) -> str:
        return self.thead.as_text() + "\n" + self.tbody.as_text()

    def as_html(self) -> SafeHtml:
        thead = self.thead.as_html()
        tbody = self.tbody.as_html()
        inner = SafeHtml.block_join([thead, tbody])
        return build_tag(tag="table", inner=inner)

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TableNode":
        thead_elem, tbody_elem = get_two_block_children(elem)
        thead = THeadNode.from_tag_element(thead_elem)
        tbody = TBodyNode.from_tag_element(tbody_elem)
        return TableNode(thead=thead, tbody=tbody)


"""
We use some helper classes for custom Zulip widgets.

Some of these should possibly be used outside the context
of custom Zulip widgets.
"""


class InlineImageChildImgNode(BaseNode):
    animated: bool
    src: str
    original_dimensions: str | None
    original_content_type: str | None

    def as_text(self) -> str:
        return f"(img {self.src})"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="img",
            inner=SafeHtml.trust(""),
            data_animated="true" if self.animated else None,
            data_original_content_type=self.original_content_type,
            data_original_dimensions=self.original_dimensions,
            src=self.src,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "InlineImageChildImgNode":
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


"""
The following classes can be considered to be
somewhat "custom" to Zulip. The incoming
markup generally uses class attributes to denote the
special Zulip constructs.
"""


class InlineImageNode(DivNode):
    img: InlineImageChildImgNode
    href: str
    title: str | None

    def as_text(self) -> str:
        return f"INLINE IMAGE: {self.href}"

    @staticmethod
    def zulip_class() -> str:
        return "message_inline_image"

    def as_html(self) -> SafeHtml:
        anchor = build_tag(
            tag="a",
            inner=self.img.as_html(),
            href=self.href,
            title=self.title,
        )
        return build_tag(
            tag="div",
            inner=anchor,
            class_=self.zulip_class(),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "InlineImageNode":
        restrict(elem, "div", "class")
        ensure_class(elem, "message_inline_image")
        anchor = get_only_child(elem, "a")
        restrict(anchor, "a", "href", "title")
        href = get_string(anchor, "href")
        title = maybe_get_string(anchor, "title")
        img = get_only_child(anchor, "img")

        return InlineImageNode(
            img=InlineImageChildImgNode.from_tag_element(img),
            href=href,
            title=title,
        )


class InlineVideoNode(DivNode):
    href: str
    src: str
    title: str | None

    def as_text(self) -> str:
        return f"INLINE VIDEO: {self.href}"

    @staticmethod
    def zulip_class() -> str:
        return "message_inline_image message_inline_video"

    def as_html(self) -> SafeHtml:
        video = build_tag(
            tag="video",
            inner=SafeHtml.trust(""),
            preload="metadata",
            src=self.src,
        )
        anchor = build_tag(
            tag="a",
            inner=video,
            href=self.href,
            title=self.title,
        )
        return build_tag(tag="div", inner=anchor, class_=self.zulip_class())

    @staticmethod
    def from_tag_element(elem: TagElement) -> "InlineVideoNode":
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


class SpoilerContentNode(ContainerNode):
    # we only need this silly field in order to
    # do round trip testing
    aria_attribute_comes_first: bool

    @staticmethod
    def zulip_class() -> str:
        return "spoiler-content"

    def as_html(self) -> SafeHtml:
        class_ = self.zulip_class()
        if self.aria_attribute_comes_first:
            return self.tag("div", aria_hidden="true", class_=class_)
        else:
            return self.tag("div", class_=class_, aria_hidden="true")

    @staticmethod
    def from_tag_element(elem: TagElement) -> "SpoilerContentNode":
        restrict(elem, "div", "class", "aria-hidden")
        ensure_class(elem, "spoiler-content")
        ensure_attribute(elem, "aria-hidden", "true")
        aria_attribute_comes_first = list(elem.attrib.keys())[0] == "aria-hidden"
        return SpoilerContentNode(
            children=get_child_nodes(elem),
            aria_attribute_comes_first=aria_attribute_comes_first,
        )


class SpoilerHeaderNode(ContainerNode):
    @staticmethod
    def zulip_class() -> str:
        return "spoiler-header"

    def as_html(self) -> SafeHtml:
        return self.block_tag("div", class_=self.zulip_class())

    @staticmethod
    def from_tag_element(elem: TagElement) -> "SpoilerHeaderNode":
        restrict(elem, "div", "class")
        ensure_class(elem, "spoiler-header")
        return SpoilerHeaderNode(children=get_child_nodes(elem, ignore_newlines=True))


class SpoilerNode(DivNode):
    header: SpoilerHeaderNode
    content: SpoilerContentNode

    def as_text(self) -> str:
        header = self.header.as_text()
        content = self.content.as_text()
        return f"SPOILER: {header}\nHIDDEN:\n{content}\nENDHIDDEN\n"

    @staticmethod
    def zulip_class() -> str:
        return "spoiler-block"

    def as_html(self) -> SafeHtml:
        header = self.header.as_html()
        content = self.content.as_html()
        return build_tag(
            tag="div",
            inner=SafeHtml.combine([header, content]),
            class_=self.zulip_class(),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "SpoilerNode":
        restrict(elem, "div", "class")
        ensure_class(elem, "spoiler-block")
        header_elem, content_elem = get_two_children(elem)
        header = SpoilerHeaderNode.from_tag_element(header_elem)
        content = SpoilerContentNode.from_tag_element(content_elem)
        return SpoilerNode(header=header, content=content)


"""
MENTIONS:

Zulip supports many different styles of mentioning users.
"""


class MentionNode(SpanNode, ABC):
    @staticmethod
    def maybe_from_tag_element(elem: TagElement) -> Optional["MentionNode"]:
        loud = LoudMentionNode.maybe_from_tag_element(elem)
        if loud is not None:
            return loud

        silent = SilentMentionNode.maybe_from_tag_element(elem)
        if silent is not None:
            return silent

        return None


class LoudMentionNode(MentionNode, ABC):
    @staticmethod
    def maybe_from_tag_element(elem: TagElement) -> Optional["LoudMentionNode"]:
        if elem.tag != "span":
            return None

        elem_class = get_string(elem, "class")

        if elem_class == "topic-mention":
            return TopicMentionNode.from_tag_element(elem)
        if elem_class == "user-group-mention":
            return UserGroupMentionNode.from_tag_element(elem)
        if elem_class == "user-mention channel-wildcard-mention":
            return ChannelWildcardMentionNode.from_tag_element(elem)
        if elem_class == "user-mention":
            return UserMentionNode.from_tag_element(elem)

        return None


class SilentMentionNode(MentionNode, ABC):
    @staticmethod
    def maybe_from_tag_element(elem: TagElement) -> Optional["SilentMentionNode"]:
        if elem.tag != "span":
            return None

        elem_class = get_string(elem, "class")

        if elem_class == "topic-mention silent":
            return TopicMentionSilentNode.from_tag_element(elem)
        if elem_class == "user-group-mention silent":
            return UserGroupMentionSilentNode.from_tag_element(elem)
        if elem_class == "user-mention channel-wildcard-mention silent":
            return ChannelWildcardMentionSilentNode.from_tag_element(elem)
        if elem_class == "user-mention silent":
            return UserMentionSilentNode.from_tag_element(elem)

        return None


class ChannelWildcardMentionNode(LoudMentionNode):
    name: Literal["@all", "@channel", "@everyone"]

    def as_text(self) -> str:
        return f"[ WILDCARD {self.name}]"

    @staticmethod
    def zulip_class() -> str:
        return "user-mention channel-wildcard-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id="*",
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "ChannelWildcardMentionNode":
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


class ChannelWildcardMentionSilentNode(SilentMentionNode):
    name: Literal["all", "channel", "everyone"]

    def as_text(self) -> str:
        return f"[ WILDCARD {self.name}]"

    @staticmethod
    def zulip_class() -> str:
        return "user-mention channel-wildcard-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id="*",
        )

    @staticmethod
    def from_tag_element(
        elem: TagElement,
    ) -> "ChannelWildcardMentionSilentNode":
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


class TopicMentionNode(LoudMentionNode):
    def as_text(self) -> str:
        return "@**topic**"

    @staticmethod
    def zulip_class() -> str:
        return "topic-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text("@topic"),
            class_=self.zulip_class(),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TopicMentionNode":
        restrict(elem, "span", "class")
        name = ensure_only_text(elem)
        if name != "@topic":
            raise IllegalMessage("bad wildcard mention")
        ensure_class(elem, "topic-mention")
        return TopicMentionNode()


class TopicMentionSilentNode(SilentMentionNode):
    def as_text(self) -> str:
        return "@_**topic**"

    @staticmethod
    def zulip_class() -> str:
        return "topic-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text("topic"),
            class_=self.zulip_class(),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TopicMentionSilentNode":
        restrict(elem, "span", "class")
        name = ensure_only_text(elem)
        if name != "topic":
            raise IllegalMessage("bad wildcard mention")
        ensure_class(elem, "topic-mention silent")
        return TopicMentionSilentNode()


class UserGroupMentionNode(LoudMentionNode):
    name: str
    group_id: int

    def as_text(self) -> str:
        return f"[ GROUP {self.name} {self.group_id} ]"

    @staticmethod
    def zulip_class() -> str:
        return "user-group-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_group_id=str(self.group_id),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "UserGroupMentionNode":
        restrict(elem, "span", "class", "data-user-group-id")
        ensure_class(elem, "user-group-mention")
        name = ensure_only_text(elem)
        group_id = get_database_id(elem, "data-user-group-id")
        return UserGroupMentionNode(name=name, group_id=group_id)


class UserGroupMentionSilentNode(SilentMentionNode):
    name: str
    group_id: int

    def as_text(self) -> str:
        return f"[ GROUP _{self.name} {self.group_id} ]"

    @staticmethod
    def zulip_class() -> str:
        return "user-group-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_group_id=str(self.group_id),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "UserGroupMentionSilentNode":
        restrict(elem, "span", "class", "data-user-group-id")
        ensure_class(elem, "user-group-mention silent")
        name = ensure_only_text(elem)
        group_id = get_database_id(elem, "data-user-group-id")
        return UserGroupMentionSilentNode(name=name, group_id=group_id)


class UserMentionNode(LoudMentionNode):
    name: str
    user_id: int

    def as_text(self) -> str:
        return f"[ {self.name} {self.user_id} ]"

    @staticmethod
    def zulip_class() -> str:
        return "user-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id=str(self.user_id),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "UserMentionNode":
        restrict(elem, "span", "class", "data-user-id")
        ensure_class(elem, "user-mention")
        name = ensure_only_text(elem)
        user_id = get_database_id(elem, "data-user-id")
        return UserMentionNode(name=name, user_id=user_id)


class UserMentionSilentNode(SilentMentionNode):
    name: str
    user_id: int

    def as_text(self) -> str:
        return f"[ _{self.name} {self.user_id} ]"

    @staticmethod
    def zulip_class() -> str:
        return "user-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id=str(self.user_id),
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "UserMentionSilentNode":
        restrict(elem, "span", "class", "data-user-id")
        ensure_class(elem, "user-mention silent")
        name = ensure_only_text(elem)
        user_id = get_database_id(elem, "data-user-id")
        return UserMentionSilentNode(name=name, user_id=user_id)


"""
I'm actually a bit unclear on whether Zulip's time widget
should be considered a custom control or not.

The HTML that gets rendered has no special
HTML class attached to the <time> tag.

Typical markdown is <time:2025-07-16T20:00:00-04:00>
"""


class TimeWidgetNode(PhrasingNode):
    datetime: str
    text: str

    def as_text(self) -> str:
        return self.text

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="time",
            inner=escape_text(self.text),
            datetime=self.datetime,
        )

    @staticmethod
    def from_tag_element(elem: TagElement) -> "TimeWidgetNode":
        restrict(elem, "time", "datetime")
        datetime = get_string(elem, "datetime")
        text = ensure_only_text(elem)
        return TimeWidgetNode(datetime=datetime, text=text)


"""
For the two major third-party plugins (pygments and katex),
we just have the caller pass us in the raw html, and we defer all
the security/performance/accuracy considerations to them.
"""


class KatexNode(SpanNode):
    html: SafeHtml
    tag_class: str

    def as_text(self) -> str:
        return f"<<<some katex html (not shown) with {self.tag_class} class>>>"

    def as_html(self) -> SafeHtml:
        return self.html

    @staticmethod
    def from_tag_element(elem: TagElement) -> "KatexNode":
        restrict(elem, "span", "class")
        tag_class = get_class(elem, "katex", "katex-display")
        html = get_html(elem)
        return KatexNode(html=SafeHtml.trust(html), tag_class=tag_class)


class PygmentsCodeBlockNode(DivNode):
    html: SafeHtml
    lang: str | None
    content: str

    def as_text(self) -> str:
        return f"\n~~~~~~~~ lang: {self.lang}\n{self.content}~~~~~~~~\n"

    def as_html(self) -> SafeHtml:
        return self.html

    @staticmethod
    def from_tag_element(elem: TagElement) -> "PygmentsCodeBlockNode":
        restrict(elem, "div", "class", "data-code-language")
        html = get_html(elem)
        lang = maybe_get_string(elem, "data-code-language")
        content = text_content(elem)
        return PygmentsCodeBlockNode(
            html=SafeHtml.trust(html), lang=lang, content=content
        )


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


@verify_round_trip
def get_node(elem: TagElement) -> BaseNode:
    node = PhrasingNode.maybe_get_from_element(elem)
    if node is not None:
        return node

    if elem.tag == "blockquote":
        return BlockQuoteNode.from_tag_element(elem)

    if elem.tag == "body":
        restrict_attributes(elem)
        return BodyNode(children=get_child_nodes(elem))

    if elem.tag == "div":
        return DivNode.from_tag_element(elem)

    if elem.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        return HeadingNode.from_tag_element(elem)

    if elem.tag == "hr":
        return ThematicBreakNode.from_tag_element(elem)

    if elem.tag in ["ol", "ul"]:
        return ListNode.from_tag_element(elem)

    if elem.tag == "p":
        return ParagraphNode.from_tag_element(elem)

    if elem.tag == "table":
        return TableNode.from_tag_element(elem)

    raise IllegalMessage(f"Unsupported tag {elem.tag}")
