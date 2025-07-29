import re

from pydantic import BaseModel


class SafeHtml(BaseModel):
    """
    The SafeHtml class doesn't magically prevent you from
    creating unsafe HTML, but it prevents a lot of obvious
    errors with the help of mypy.

    You should never directly instantiate SafeHtml objects.

    Only call SafeHtml.trust for strings that you either trust
    or that you have properly escaped.

    The SafeHtml protocol also prevents you from accidentally
    double-escaping strings (but again, not completely fool-proof).
    """

    html_that_we_trust: str

    def __str__(self) -> str:
        return self.html_that_we_trust

    @staticmethod
    def trust(s: str) -> "SafeHtml":
        return SafeHtml(html_that_we_trust=s)

    @staticmethod
    def combine(items: list["SafeHtml"]) -> "SafeHtml":
        return SafeHtml.trust("".join(str(item) for item in items))

    @staticmethod
    def block_join(items: list["SafeHtml"]) -> "SafeHtml":
        if not items:
            return SafeHtml.trust("\n")
        return SafeHtml.trust("\n" + "\n".join(str(item) for item in items) + "\n")


def build_tag(*, tag: str, inner: SafeHtml, **attrs: str | None) -> SafeHtml:
    attr_suffix = "".join(
        f''' {attr.rstrip("_").replace("_", "-")}="{escape_text(value, replace_quotes=True)}"'''
        for attr, value in attrs.items()
        if value is not None
    )
    if str(inner) == "":
        return SafeHtml.trust(f"<{tag}{attr_suffix}/>")
    return SafeHtml.trust(f"<{tag}{attr_suffix}>{inner}</{tag}>")


def canonicalize_escape_text(text: str) -> str:
    def replace(m: re.Match[str]) -> str:
        n = int(m.group(1), 16)
        return f"&#{n};"

    return re.sub(r"&#x(.*?);", replace, text)


def escape_text(text: str, replace_quotes: bool = False) -> SafeHtml:
    # This is very similar to html.escape, but we want to match the
    # lxml output for now.  The lxml parser is annoying in that
    # it doesn't easily round trip the original HTML.
    text = text.replace("&", "&amp;")
    special_chars = [c for c in text if ord(c) > 128]
    for c in special_chars:
        text = text.replace(c, f"&#{ord(c)};")
    text = text.replace(">", "&gt;")
    text = text.replace("<", "&lt;")
    if replace_quotes:
        text = text.replace('"', "&quot;")
    return SafeHtml.trust(text)
