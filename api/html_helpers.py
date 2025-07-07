class SafeHtml:
    """
    The SafeHtml class doesn't magically prevent you from
    creating unsafe HTML, but it prevents a lot of obvious
    errors with the help of mypy.

    You should only directly instantiate SafeHtml objects
    from strings that you either trust or that you have
    properly escaped.

    The SafeHtml protocol also prevents you from accidentally
    double-escaping strings (but again, not completely fool-proof).
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text

    @staticmethod
    def combine(items: list["SafeHtml"]) -> "SafeHtml":
        return SafeHtml("".join(str(item) for item in items))

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
