from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseNode(BaseModel, ABC):
    @abstractmethod
    def as_text(self) -> str:
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

Also, during this stage of development, I use RawNode as a
catch-all class for obscure corner cases that I haven't encountered
yet, and then my demo app just spews out raw HTML as bare text.
"""


class RawNode(BaseNode):
    html: str

    def as_text(self) -> str:
        return self.html


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


"""
The following classes can be considered to be
somewhat "custom" to Zulip. The incoming
markup generally uses class attributes to denote the
special Zulip constructs.
"""


class CodeBlockNode(BaseNode):
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


class EmojiImageNode(BaseNode):
    src: str
    title: str

    def as_text(self) -> str:
        return f":{self.title}:"


class EmojiSpanNode(BaseNode):
    unicodes: list[str]
    title: str

    def as_text(self) -> str:
        c = " ".join(chr(int(unicode, 16)) for unicode in self.unicodes)
        return f"{c} (:{self.title})"


class InlineImageNode(BaseNode):
    href: str
    title: str
    src: str
    animated: bool
    original_dimensions: str
    original_content_type: str

    def as_text(self) -> str:
        return f"INLINE IMAGE: {self.href}"


class InlineVideoNode(BaseNode):
    href: str

    def as_text(self) -> str:
        return f"INLINE VIDEO: {self.href}"


class MessageLinkNode(BaseNode):
    href: str
    children: list[BaseNode]

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text} (MESSAGE LINK: {self.href})]"


class SpoilerNode(BaseNode):
    header: BaseNode
    content: BaseNode

    def as_text(self) -> str:
        header = self.header.as_text()
        content = self.content.as_text()
        return f"SPOILER: {header}\nHIDDEN:\n{content}\nENDHIDDEN\n"


class StreamLinkNode(BaseNode):
    href: str
    stream_id: str
    children: list[BaseNode]
    has_topic: bool

    def as_text(self) -> str:
        text = " ".join(c.as_text() for c in self.children)
        return f"[{text}] ({self.href}) (stream id {self.stream_id}, has_topic: {self.has_topic})"


class TimeWidgetNode(BaseNode):
    datetime: str
    text: str

    def as_text(self) -> str:
        return self.text


class UserGroupMentionNode(BaseNode):
    name: str
    group_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ GROUP {'_' if self.silent else ''}{self.name} {self.group_id} ]"


class UserMentionNode(BaseNode):
    name: str
    user_id: str
    silent: bool

    def as_text(self) -> str:
        return f"[ {'_' if self.silent else ''}{self.name} {self.user_id} ]"


"""
We have nodes for things like the <a> and <br> tag
for cases where Zulip uses them in pretty generic
ways.
"""


class AnchorNode(BaseNode):
    href: str
    children: list[BaseNode]

    def as_text(self) -> str:
        content = "".join(c.as_text() for c in self.children)
        return f"[{content}]({self.href})"


class BreakNode(BaseNode):
    def as_text(self) -> str:
        return "\n"


class HrNode(BaseNode):
    def as_text(self) -> str:
        return "\n\n---\n\n"


"""
Subclasses of ContainerNode tend to be pretty vanilla,
and in the Zulip markdown you have no special
attributes ("class" or otherwise) on the start tags.
"""


class ContainerNode(BaseNode):
    children: list[BaseNode]

    def children_text(self) -> str:
        return " ".join(c.as_text() for c in self.children)

    def as_text(self) -> str:
        return self.children_text()


"""
The various subclasses of ContainerNode are below.

Generally it's up to the calling code to map these into some
kind of UI paradigm.  The as_text methods are basically
for debugging and convenience.  For example, if you try
to build a UI to show a Zulip message, you can fall
back to the as_text() methods and just stick the text
into a text widget until you're ready to flesh out the UI.
"""


class BlockQuoteNode(ContainerNode):
    def as_text(self) -> str:
        content = self.children_text()
        return f"\n-----\n{content}\n-----\n"


class BodyNode(ContainerNode):
    pass


class CodeNode(ContainerNode):
    def as_text(self) -> str:
        return f"`{self.children_text()}`"


class DelNode(ContainerNode):
    def as_text(self) -> str:
        return f"~~{self.children_text()}~~"


class EmNode(ContainerNode):
    def as_text(self) -> str:
        return f"*{self.children_text()}*"


class Header1Node(ContainerNode):
    def as_text(self) -> str:
        return f"# {self.children_text()}\n\n"


class Header2Node(ContainerNode):
    def as_text(self) -> str:
        return f"## {self.children_text()}\n\n"


class Header3Node(ContainerNode):
    def as_text(self) -> str:
        return f"### {self.children_text()}\n\n"


class Header4Node(ContainerNode):
    def as_text(self) -> str:
        return f"#### {self.children_text()}\n\n"


class Header5Node(ContainerNode):
    def as_text(self) -> str:
        return f"##### {self.children_text()}\n\n"


class Header6Node(ContainerNode):
    def as_text(self) -> str:
        return f"###### {self.children_text()}\n\n"


class ListItemNode(ContainerNode):
    pass


class OrderedListNode(ContainerNode):
    def as_text(self) -> str:
        return "".join(
            f"\n    {i}. " + c.as_text() for i, c in enumerate(self.children)
        )


class ParagraphNode(ContainerNode):
    def as_text(self) -> str:
        return self.children_text() + "\n\n"


class StrongNode(ContainerNode):
    def as_text(self) -> str:
        return f"**{self.children_text()}**"


class UnorderedListNode(ContainerNode):
    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)
