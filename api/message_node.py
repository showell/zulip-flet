from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseNode(BaseModel, ABC):
    @abstractmethod
    def as_text(self) -> str:
        pass


class RawNode(BaseNode):
    text: str

    def as_text(self) -> str:
        return self.text


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


"""
Subclasses of ContainerNode tend to be pretty vanilla,
and in the Zulip markdown you have no special
attributes ("class" or otherwise) on the start tags.
"""


class ContainerNode(BaseNode):
    children: list[BaseNode]

    def as_text(self) -> str:
        return " ".join(c.as_text() for c in self.children)


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
        content = "".join(c.as_text() for c in self.children)
        return f"\n-----\n{content}\n-----\n"


class BodyNode(ContainerNode):
    pass


class CodeNode(ContainerNode):
    def as_text(self) -> str:
        return f"`{''.join(c.as_text() for c in self.children)}`"


class EmNode(ContainerNode):
    def as_text(self) -> str:
        return f"*{''.join(c.as_text() for c in self.children)}*"


class ListItemNode(ContainerNode):
    pass


class OrderedListNode(ContainerNode):
    def as_text(self) -> str:
        return "".join(
            f"\n    {i}. " + c.as_text() for i, c in enumerate(self.children)
        )


class ParagraphNode(ContainerNode):
    def as_text(self) -> str:
        return " ".join(c.as_text() for c in self.children) + "\n\n"


class StrongNode(ContainerNode):
    def as_text(self) -> str:
        return f"**{''.join(c.as_text() for c in self.children)}**"


class UnorderedListNode(ContainerNode):
    def as_text(self) -> str:
        return "".join("\n    - " + c.as_text() for c in self.children)
