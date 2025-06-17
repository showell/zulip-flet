from lxml import etree

def get_text(elem):
    text = elem.text or ""
    text += "".join(get_text(c) for c in elem)
    return text

def text_content(html):
    root = etree.HTML("<html>" + html + "</html>")
    return get_text(root)

