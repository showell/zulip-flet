from lxml import etree

def text_content(html):
    root = etree.HTML("<html>" + html + "</html>")
    return "raw html: " + etree.tostring(root).decode("utf8")

