import html

from .text import Text
from .element import Element

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]

HEAD_TAGS = [
    "base", "basefont", "bgsound", "noscript",
    "link", "meta", "title", "style", "script",
]

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
    
    def parse_html(self):
        buffer = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if buffer:
                    self.add_text(buffer)
                buffer = ""
            elif c == ">":
                in_tag = False
                self.add_tag(buffer)
                buffer = ""
            else:
                buffer += c
        
        if buffer:
            if in_tag:
                self.add_text(("<" + buffer))
            else:
                self.add_tag(buffer)
                
        return self.finish()
        
    def add_text(self, text):
        if text.isspace(): return
        self.implicit_tags(None)
        if not self.unfinished:
            return
        parent = self.unfinished[-1]
        node = Text(html.unescape(text), parent)
        parent.children.append(node)
        
    def add_tag(self, tag):
        tag, attributes = self.get_attributes(tag)
        if tag.startswith("!"):
            return
        self.implicit_tags(tag)
        if tag.startswith("/"):
            closing_tag = tag [1:]
            
            if len(self.unfinished) == 1:
                return
            
            if self.unfinished[-1].tag != closing_tag:
                return
            
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)
    
    def get_attributes(self, text):
        parts = []
        current = ""
        quote = None
        for char in text:
            if char in ("'", '"'):
                if quote == char:
                    quote = None
                elif quote is None:
                    quote = char
                current += char
            elif char.isspace() and quote is None:
                if current:
                    parts.append(current)
                    current = ""
            else:
                current += char
        if current:
            parts.append(current)

        if not parts:
            return "", {}
        tag = parts[0].casefold()
        attributes = {}
        for attrpair in parts[1:]:
            if "=" in attrpair:
                key, value = attrpair.split("=", 1)
                if len(value) > 1 and value[0] in ("'", '"') and value[-1] == value[0]:
                    value = value[1:-1]
                attributes[key.casefold()] = html.unescape(value)
            else:
                attributes[attrpair.casefold()] = ""

        return tag, attributes
            
    def finish(self):
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        return self.unfinished.pop()
    
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] \
                and tag not in ["head", "body", "/html"]:
                    if tag in HEAD_TAGS:
                        self.add_tag("head")
                    else:
                        self.add_tag("body")
            elif open_tags == ["html", "head"] and \
                tag not in ["head", "/head"] + HEAD_TAGS:
                    self.add_tag("/head")
            else:
                break
    
def print_tree(node, indent = 0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
