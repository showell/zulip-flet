from abc import ABC, abstractmethod
from typing import Literal, Sequence

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
    pass


class SpanNode(PhrasingNode, ABC):
    pass


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


class ThematicBreakNode(BaseNode):
    def as_text(self) -> str:
        return "\n\n---\n\n"

    def as_html(self) -> SafeHtml:
        return SafeHtml.trust("<hr/>")


"""
Here we define a ContainerNode class. Essentially, containers
have arbitrary children.

Note that there are some classes in our AST that do have
children but don't inherit from ContainerNode.  This means
that they are something like tables or lists, in which their
child nodes are way more constrained.

We eventually want more refinement here.
"""


class ContainerNode(BaseNode):
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
Whenever practical, we try to stay at the same layer of
abstraction as the mdast project.

See https://github.com/syntax-tree/mdast?tab=readme-ov-file#heading
as an example.  Instead of concretely having distinct classes for
<h1>, <h2>, etc. in my AST, we use a Heading concept with depth.
"""


class HeadingNode(ContainerNode):
    children: Sequence[PhrasingNode]
    depth: int = Field(ge=1, le=6)

    def as_text(self) -> str:
        return f"{'#' * self.depth} {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag(f"h{self.depth}")


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

    Delete == StrikeThrough == <del>foo</del> == ~~foo~~
    Emphasis == <em>foo</em> == *foo*
    Strong == <strong>foo</strong> == **foo* 
"""


class TextFormattingNode(ContainerNode, PhrasingNode, ABC):
    pass


class DeleteNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"~~{self.children_text()}~~"

    def as_html(self) -> SafeHtml:
        return self.tag("del")


class EmphasisNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"*{self.children_text()}*"

    def as_html(self) -> SafeHtml:
        return self.tag("em")


class StrongNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"**{self.children_text()}**"

    def as_html(self) -> SafeHtml:
        return self.tag("strong")


"""
We have error nodes
"""


class ParseErrorNode(PhrasingNode):
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


class TimeStampErrorNode(SpanNode, ParseErrorNode):
    text: str

    def as_text(self) -> str:
        return "timestamp error"

    def zulip_class(self) -> str:
        return "timestamp-error"


"""
And then some more basic classes follow.
"""


class LinkNode(PhrasingNode):
    pass


class AnchorNode(LinkNode, ContainerNode):
    href: str

    def as_text(self) -> str:
        content = "".join(c.as_text() for c in self.children)
        return f"[{content}] ({self.href})"

    def as_html(self) -> SafeHtml:
        return self.tag("a", href=self.href)


class BlockQuoteNode(ContainerNode):
    def as_text(self) -> str:
        content = self.children_text()
        return f"\n-----\n{content}\n-----\n"

    def as_html(self) -> SafeHtml:
        return self.tag("blockquote")


class BodyNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.tag("body")


class CodeNode(TextFormattingNode):
    def as_text(self) -> str:
        return f"`{self.children_text()}`"

    def as_html(self) -> SafeHtml:
        return self.tag("code")


class ParagraphNode(ContainerNode):
    def as_text(self) -> str:
        return self.children_text() + "\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("p")


"""
Lists
"""


class ListItemNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.tag("li")


class OrderedListNode(BaseNode):
    children: Sequence[ListItemNode]
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


class UnorderedListNode(BaseNode):
    children: Sequence[ListItemNode]

    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)

    def as_html(self) -> SafeHtml:
        list_items = SafeHtml.block_join([c.as_html() for c in self.children])
        return build_tag(
            tag="ul",
            inner=list_items,
        )


"""
Zulip tables are their own special beast.  Zulip, to my knowledge,
doesn't do anything custom with the actual conversion of Markdown
tables into HTML tables, but we need to get granular on the description
of tables, since the headers and cells of Zulip tables **can**
include custom thingies.
"""


class ThNode(ContainerNode):
    text_align: str | None

    def as_text(self) -> str:
        return f"    TH: {self.children_text()} ({self.text_align})\n"

    def as_html(self) -> SafeHtml:
        style = f"text-align: {self.text_align};" if self.text_align else None
        return self.tag("th", style=style)


class TdNode(ContainerNode):
    text_align: str | None

    def as_text(self) -> str:
        return f"    TD: {self.children_text()} ({self.text_align})\n"

    def as_html(self) -> SafeHtml:
        style = f"text-align: {self.text_align};" if self.text_align else None
        return self.tag("td", style=style)


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


class TBodyNode(BaseNode):
    trs: Sequence[TrNode]

    def as_text(self) -> str:
        tr_text = "".join(tr.as_text() for tr in self.trs)
        return f"\n-----------\n{tr_text}"

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.block_join([tr.as_html() for tr in self.trs])
        return build_tag(tag="tbody", inner=inner)


class THeadNode(BaseNode):
    ths: Sequence[ThNode]

    def as_text(self) -> str:
        th_text = "".join(th.as_text() for th in self.ths)
        return f"\n-----------\n{th_text}"

    def as_html(self) -> SafeHtml:
        ths = SafeHtml.block_join([th.as_html() for th in self.ths])
        tr = build_tag(tag="tr", inner=ths)
        return build_tag(tag="thead", inner=SafeHtml.block_join([tr]))


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


"""
The following classes can be considered to be
somewhat "custom" to Zulip. The incoming
markup generally uses class attributes to denote the
special Zulip constructs.
"""


class ChannelWildcardMentionNode(SpanNode):
    name: Literal["@all", "@channel", "@everyone"]

    def as_text(self) -> str:
        return f"[ WILDCARD {self.name}]"

    def zulip_class(self) -> str:
        return "user-mention channel-wildcard-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id="*",
        )


class ChannelWildcardMentionSilentNode(SpanNode):
    name: Literal["all", "channel", "everyone"]

    def as_text(self) -> str:
        return f"[ WILDCARD {self.name}]"

    def zulip_class(self) -> str:
        return "user-mention channel-wildcard-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id="*",
        )


class EmojiImageNode(LinkNode):
    src: str
    title: str

    def as_text(self) -> str:
        return f":{self.title}:"

    def zulip_class(self) -> str:
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


class EmojiSpanNode(SpanNode):
    unicodes: Sequence[str]
    title: str

    def as_text(self) -> str:
        c = " ".join(chr(int(unicode, 16)) for unicode in self.unicodes)
        return f"{c} (:{self.title})"

    def zulip_class(self) -> str:
        unicode_suffix = "-".join(self.unicodes)
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


class InlineImageNode(BaseNode):
    img: InlineImageChildImgNode
    href: str
    title: str | None

    def as_text(self) -> str:
        return f"INLINE IMAGE: {self.href}"

    def zulip_class(self) -> str:
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


class InlineVideoNode(BaseNode):
    href: str
    src: str
    title: str | None

    def as_text(self) -> str:
        return f"INLINE VIDEO: {self.href}"

    def zulip_class(self) -> str:
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


class MessageLinkNode(LinkNode, ContainerNode):
    href: str

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text} (MESSAGE LINK: {self.href})]"

    def zulip_class(self) -> str:
        return "message-link"

    def as_html(self) -> SafeHtml:
        href = self.href
        return self.tag("a", class_=self.zulip_class(), href=href)


class SpoilerContentNode(ContainerNode):
    # we only need this silly field in order to
    # do round trip testing
    aria_attribute_comes_first: bool

    def zulip_class(self) -> str:
        return "spoiler-content"

    def as_html(self) -> SafeHtml:
        class_ = self.zulip_class()
        if self.aria_attribute_comes_first:
            return self.tag("div", aria_hidden="true", class_=class_)
        else:
            return self.tag("div", class_=class_, aria_hidden="true")


class SpoilerHeaderNode(ContainerNode):
    def zulip_class(self) -> str:
        return "spoiler-header"

    def as_html(self) -> SafeHtml:
        return self.block_tag("div", class_=self.zulip_class())


class SpoilerNode(BaseNode):
    header: SpoilerHeaderNode
    content: SpoilerContentNode

    def as_text(self) -> str:
        header = self.header.as_text()
        content = self.content.as_text()
        return f"SPOILER: {header}\nHIDDEN:\n{content}\nENDHIDDEN\n"

    def zulip_class(self) -> str:
        return "spoiler-block"

    def as_html(self) -> SafeHtml:
        header = self.header.as_html()
        content = self.content.as_html()
        return build_tag(
            tag="div",
            inner=SafeHtml.combine([header, content]),
            class_=self.zulip_class(),
        )


class StreamLinkNode(LinkNode, ContainerNode):
    href: str
    stream_id: int
    has_topic: bool

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text}] ({self.href}) (stream id {self.stream_id}, has_topic: {self.has_topic})"

    def zulip_class(self) -> str:
        return "stream-topic" if self.has_topic else "stream"

    def as_html(self) -> SafeHtml:
        return self.tag(
            "a",
            class_=self.zulip_class(),
            data_stream_id=str(self.stream_id),
            href=self.href,
        )


class TopicMentionNode(SpanNode):
    def as_text(self) -> str:
        return "@**topic**"

    def zulip_class(self) -> str:
        return "topic-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text("@topic"),
            class_=self.zulip_class(),
        )


class TopicMentionSilentNode(SpanNode):
    def as_text(self) -> str:
        return "@_**topic**"

    def zulip_class(self) -> str:
        return "topic-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text("topic"),
            class_=self.zulip_class(),
        )


class UserGroupMentionNode(SpanNode):
    name: str
    group_id: int

    def as_text(self) -> str:
        return f"[ GROUP {self.name} {self.group_id} ]"

    def zulip_class(self) -> str:
        return "user-group-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_group_id=str(self.group_id),
        )


class UserGroupMentionSilentNode(SpanNode):
    name: str
    group_id: int

    def as_text(self) -> str:
        return f"[ GROUP _{self.name} {self.group_id} ]"

    def zulip_class(self) -> str:
        return "user-group-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_group_id=str(self.group_id),
        )


class UserMentionNode(SpanNode):
    name: str
    user_id: int

    def as_text(self) -> str:
        return f"[ {self.name} {self.user_id} ]"

    def zulip_class(self) -> str:
        return "user-mention"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id=str(self.user_id),
        )


class UserMentionSilentNode(SpanNode):
    name: str
    user_id: int

    def as_text(self) -> str:
        return f"[ _{self.name} {self.user_id} ]"

    def zulip_class(self) -> str:
        return "user-mention silent"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=self.zulip_class(),
            data_user_id=str(self.user_id),
        )


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


class PygmentsCodeBlockNode(BaseNode):
    html: SafeHtml
    lang: str | None
    content: str

    def as_text(self) -> str:
        return f"\n~~~~~~~~ lang: {self.lang}\n{self.content}~~~~~~~~\n"

    def as_html(self) -> SafeHtml:
        return self.html
