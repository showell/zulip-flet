from html_element import TagElement, get_only_child, restrict
from lxml import etree
from message_node import ZulipContent


def get_message_node(html: str) -> ZulipContent:
    # We try to be strict, but lxml doesn't like math/video/time and doesn't
    # recover from certain <br> tags in paragraphs.
    if (
        "<math" in html
        or "<video" in html
        or "<audio" in html
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
    message_node = ZulipContent.from_tag_element(body)
    return message_node
