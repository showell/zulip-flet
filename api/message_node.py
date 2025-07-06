from abc import ABC, abstractmethod

from pydantic import BaseModel

"""
First, we have some helpers to build HTML from the AST.
"""


class SafeHtml:
    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text

    @staticmethod
    def join(s: str, items: list["SafeHtml"]) -> "SafeHtml":
        assert s in ("", " ", "\n")
        return SafeHtml(s.join(str(item) for item in items))

    @staticmethod
    def block_join(items: list["SafeHtml"]) -> "SafeHtml":
        if not items:
            return SafeHtml("\n")
        return SafeHtml("\n" + "\n".join(str(item) for item in items) + "\n")


def build_tag(*, tag: str, inner: SafeHtml, **attrs: str | None) -> SafeHtml:
    attr_suffix = "".join(
        f''' {attr.rstrip("_").replace("_", "-")}="{escape_text(value)}"'''
        for attr, value in attrs.items()
        if value is not None
    )
    if str(inner) == "":
        return SafeHtml(f"<{tag}{attr_suffix}/>")
    return SafeHtml(f"<{tag}{attr_suffix}>{inner}</{tag}>")


def escape_text(text: str) -> SafeHtml:
    # This is very similar to html.escape, but we want to match the
    # lxml output for now.  The lxml parser is annoying in that
    # it doesn't easily round trip the original HTML.
    text = text.replace("&", "&amp;")
    special_chars = [c for c in text if ord(c) > 128]
    for c in special_chars:
        text = text.replace(c, f"&#{ord(c)};")
    text = text.replace(">", "&gt;")
    text = text.replace("<", "&lt;")
    return SafeHtml(text)


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


"""
The aim of this code is to define the structure of Zulip
messages in a semantic way, and I don't want to box myself
into particular implementation details when it comes to how
the server renders it.  In particular, I am hoping that decades
down the road, we don't even use HTML as the over-the-wire
format for telling clients what to render.  Maybe that's a bit
extreme.

Having said all that, I live in the real world in 2025.  Certain
things are very baked into HTML at this point.  And I mostly
like HTML.

In particular, we use HTML to render LaTeX via KaTeX for mathematical
typesetting, and there is no way in the near future that I want
to re-invent the wheel when it comes to producing HTML for that.

Long story short, I only choose to represent LaTeX/KaTeX blocks
as raw HTML.
"""


class RawNode(BaseNode, ABC):
    html: str

    @abstractmethod
    def as_text(self) -> str:
        pass

    def as_html(self) -> SafeHtml:
        return SafeHtml(self.html)


class RawCodeBlockNode(RawNode):
    # Note that we treat code blocks as completely
    # opaque things, and we don't want to deal with
    # all the pygments markup at this layer of the
    # software.  We assume our callers may have their
    # own alternative to pygments to render code, or
    # maybe they are even just fine with vanilla
    # code blocks.
    lang: str
    content: str

    def as_text(self) -> str:
        return f"\n~~~~~~~~ lang: {self.lang}\n{self.content}~~~~~~~~\n"


class RawKatexNode(RawNode):
    tag_class: str

    def as_text(self) -> str:
        return f"<<<some katex html (not shown) with {self.tag_class} class>>>"


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


class TextNode(BaseNode):
    text: str

    def as_text(self) -> str:
        return self.text

    def as_html(self) -> SafeHtml:
        return escape_text(self.text)


"""
Most subclasses of ContainerNode tend to be pretty vanilla,
and in the Zulip markdown you have no special
attributes ("class" or otherwise) on the start tags.

A few subclasses, such as AnchorNode, do have attributes,
and they will have extra fields for those.

Also, some of the "special" Zulip classes inherit from
ContainerNode
"""


class ContainerNode(BaseNode):
    children: list[BaseNode]

    def children_text(self) -> str:
        return " ".join(c.as_text() for c in self.children)

    def as_text(self) -> str:
        return self.children_text()

    def inner(self) -> SafeHtml:
        return SafeHtml.join("", [c.as_html() for c in self.children])

    def tag(self, tag: str, **attrs: str | None) -> SafeHtml:
        return build_tag(tag=tag, inner=self.inner(), **attrs)

    def block_tag(self, tag: str, **attrs: str | None) -> SafeHtml:
        inner = SafeHtml.block_join([c.as_html() for c in self.children])
        return build_tag(tag=tag, inner=inner, **attrs)


"""
The following classes can be considered to be
somewhat "custom" to Zulip. The incoming
markup generally uses class attributes to denote the
special Zulip constructs.
"""


class EmojiImageNode(BaseNode):
    src: str
    title: str

    def as_text(self) -> str:
        return f":{self.title}:"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="img",
            inner=SafeHtml(""),
            alt=f":{self.title.replace(' ', '_')}:",
            class_="emoji",
            src=self.src,
            title=self.title,
        )


class EmojiSpanNode(BaseNode):
    unicodes: list[str]
    title: str

    def as_text(self) -> str:
        c = " ".join(chr(int(unicode, 16)) for unicode in self.unicodes)
        return f"{c} (:{self.title})"

    def as_html(self) -> SafeHtml:
        title = self.title
        unicode_suffix = "-".join(self.unicodes)
        return build_tag(
            tag="span",
            inner=escape_text(f":{title.replace(' ', '_')}:"),
            aria_label=title,
            class_=f"emoji emoji-{unicode_suffix}",
            role="img",
            title=title,
        )


class ImgNode(BaseNode):
    animated: bool
    src: str
    original_dimensions: str | None
    original_content_type: str | None

    def as_text(self) -> str:
        return f"(img {self.src})"

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="img",
            inner=SafeHtml(""),
            data_animated="true" if self.animated else None,
            data_original_content_type=self.original_content_type,
            data_original_dimensions=self.original_dimensions,
            src=self.src,
        )


class InlineImageNode(BaseNode):
    img: ImgNode
    href: str
    title: str | None

    def as_text(self) -> str:
        return f"INLINE IMAGE: {self.href}"

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
            class_="message_inline_image",
        )


class InlineVideoNode(BaseNode):
    href: str
    src: str

    def as_text(self) -> str:
        return f"INLINE VIDEO: {self.href}"

    def as_html(self) -> SafeHtml:
        return SafeHtml("XXX")


class MessageLinkNode(ContainerNode):
    href: str

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text} (MESSAGE LINK: {self.href})]"

    def as_html(self) -> SafeHtml:
        href = self.href
        return self.tag("a", class_="message-link", href=href)


class SpoilerContentNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.block_tag("div", class_="spoiler-content", aria_hidden="true")


class SpoilerHeaderNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.block_tag("div", class_="spoiler-header")


class SpoilerNode(BaseNode):
    header: SpoilerHeaderNode
    content: SpoilerContentNode

    def as_text(self) -> str:
        header = self.header.as_text()
        content = self.content.as_text()
        return f"SPOILER: {header}\nHIDDEN:\n{content}\nENDHIDDEN\n"

    def as_html(self) -> SafeHtml:
        header = self.header.as_html()
        content = self.content.as_html()
        return SafeHtml(f"""<div class="spoiler-block">{header}{content}</div>""")


class StreamLinkNode(ContainerNode):
    href: str
    stream_id: str
    has_topic: bool

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text}] ({self.href}) (stream id {self.stream_id}, has_topic: {self.has_topic})"

    def as_html(self) -> SafeHtml:
        tag_class = "stream-topic" if self.has_topic else "stream"
        return self.tag(
            "a", class_=tag_class, data_stream_id=self.stream_id, href=self.href
        )


class TimeWidgetNode(BaseNode):
    datetime: str
    text: str

    def as_text(self) -> str:
        return self.text

    def as_html(self) -> SafeHtml:
        return build_tag(
            tag="time", inner=escape_text(self.text), datetime=self.datetime
        )


class UserGroupMentionNode(BaseNode):
    name: str
    group_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ GROUP {'_' if self.silent else ''}{self.name} {self.group_id} ]"

    def as_html(self) -> SafeHtml:
        tag_class = "user-group-mention silent" if self.silent else "user-group-mention"
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=tag_class,
            data_user_group_id=self.group_id,
        )


class UserMentionNode(BaseNode):
    name: str
    user_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ {'_' if self.silent else ''}{self.name} {self.user_id} ]"

    def as_html(self) -> SafeHtml:
        tag_class = "user-mention silent" if self.silent else "user-mention"
        return build_tag(
            tag="span",
            inner=escape_text(self.name),
            class_=tag_class,
            data_user_id=self.user_id,
        )


"""
We have nodes for things like the <br> and <hr> tags
for cases where Zulip uses them in pretty generic
ways.
"""


class BreakNode(BaseNode):
    def as_text(self) -> str:
        return "\n"

    def as_html(self) -> SafeHtml:
        return SafeHtml("<br/>")


class HrNode(BaseNode):
    def as_text(self) -> str:
        return "\n\n---\n\n"

    def as_html(self) -> SafeHtml:
        return SafeHtml("<hr/>")


"""
The mostly-vanilla subclasses of ContainerNode are below.

Generally it's up to the calling code to map these into some
kind of UI paradigm.  The as_text methods are basically
for debugging and convenience.  For example, if you try
to build a UI to show a Zulip message, you can fall
back to the as_text() methods and just stick the text
into a text widget until you're ready to flesh out the UI.
"""


class AnchorNode(ContainerNode):
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


class CodeNode(ContainerNode):
    def as_text(self) -> str:
        return f"`{self.children_text()}`"

    def as_html(self) -> SafeHtml:
        return self.tag("code")


class DelNode(ContainerNode):
    def as_text(self) -> str:
        return f"~~{self.children_text()}~~"

    def as_html(self) -> SafeHtml:
        return self.tag("del")


class EmNode(ContainerNode):
    def as_text(self) -> str:
        return f"*{self.children_text()}*"

    def as_html(self) -> SafeHtml:
        return self.tag("em")


class Header1Node(ContainerNode):
    def as_text(self) -> str:
        return f"# {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h1")


class Header2Node(ContainerNode):
    def as_text(self) -> str:
        return f"## {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h2")


class Header3Node(ContainerNode):
    def as_text(self) -> str:
        return f"### {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h3")


class Header4Node(ContainerNode):
    def as_text(self) -> str:
        return f"#### {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h4")


class Header5Node(ContainerNode):
    def as_text(self) -> str:
        return f"##### {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h5")


class Header6Node(ContainerNode):
    def as_text(self) -> str:
        return f"###### {self.children_text()}\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("h6")


class ListItemNode(ContainerNode):
    def as_html(self) -> SafeHtml:
        return self.tag("li")


class OrderedListNode(ContainerNode):
    start: int

    def as_text(self) -> str:
        return "".join(
            f"\n    {i + (self.start or 1)}. " + c.as_text()
            for i, c in enumerate(self.children)
        )

    def as_html(self) -> SafeHtml:
        if self.start:
            return self.tag("ol", start=str(self.start))
        return self.tag("ol")


class ParagraphNode(ContainerNode):
    def as_text(self) -> str:
        return self.children_text() + "\n\n"

    def as_html(self) -> SafeHtml:
        return self.tag("p")


class StrongNode(ContainerNode):
    def as_text(self) -> str:
        return f"**{self.children_text()}**"

    def as_html(self) -> SafeHtml:
        return self.tag("strong")


class UnorderedListNode(ContainerNode):
    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)

    def as_html(self) -> SafeHtml:
        return self.tag("ul")


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
    tds: list[TdNode]

    def as_text(self) -> str:
        s = "TR\n"
        for td in self.tds:
            s += td.as_text()
        s += "\n"
        return s

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.join("\n", [td.as_html() for td in self.tds])
        return SafeHtml(f"<tr>\n{inner}\n</tr>")


class TBodyNode(BaseNode):
    trs: list[TrNode]

    def as_text(self) -> str:
        tr_text = "".join(tr.as_text() for tr in self.trs)
        return f"\n-----------\n{tr_text}"

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.join("\n", [tr.as_html() for tr in self.trs])
        return SafeHtml(f"<tbody>\n{inner}\n</tbody>")


class THeadNode(BaseNode):
    ths: list[ThNode]

    def as_text(self) -> str:
        th_text = "".join(th.as_text() for th in self.ths)
        return f"\n-----------\n{th_text}"

    def as_html(self) -> SafeHtml:
        inner = SafeHtml.join("\n", [th.as_html() for th in self.ths])
        return SafeHtml(f"<thead>\n<tr>\n{inner}\n</tr>\n</thead>")


class TableNode(BaseNode):
    thead: THeadNode
    tbody: TBodyNode

    def as_text(self) -> str:
        return self.thead.as_text() + "\n" + self.tbody.as_text()

    def as_html(self) -> SafeHtml:
        return SafeHtml(
            f"<table>\n{self.thead.as_html()}\n{self.tbody.as_html()}\n</table>"
        )
