import html
import re

from .text import Text
from .element import Element

SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
]

IMPLICITLY_CLOSED_BY_SAME_TAG = {"p", "li"}

HEAD_TAGS = [
    "base", "basefont", "bgsound", "noscript",
    "link", "meta", "title", "style", "script",
]

RAW_TEXT_TAGS = {"script", "style"}

class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
    
    def parse_html(self):
        buffer = ""
        in_tag = False
        i = 0
        while i < len(self.body):
            if not in_tag and self.unfinished and \
                    self.unfinished[-1].tag in RAW_TEXT_TAGS:
                raw_tag = self.unfinished[-1].tag
                closing = re.search(
                    rf"</{raw_tag}\s*>", self.body[i:], re.IGNORECASE
                )
                if closing is None:
                    break
                i += closing.start()
                buffer = ""
                self.add_tag("/" + raw_tag)
                i += closing.end() - closing.start()
                continue

            c = self.body[i]
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
            i += 1
        
        if buffer:
            if in_tag:
                self.add_text(("<" + buffer))
            else:
                self.add_text(buffer)
                
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
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                    if tag in HEAD_TAGS:
                        self.add_tag("head")
                    else:
                        self.add_tag("body")
            elif open_tags == ["html", "head"] and \
                tag not in ["head", "/head"] + HEAD_TAGS:
                self.add_tag("/head")
            elif self.should_implicitly_close(tag, open_tags):
                self.close_open_tag(tag)
            else:
                break

    def close_open_tag(self, tag):
        while self.unfinished:
            node = self.unfinished.pop()
            parent = self.unfinished[-1] if self.unfinished else None
            if parent is not None:
                parent.children.append(node)
            if node.tag == tag:
                return

    def should_implicitly_close(self, tag, open_tags):
        if tag == "p":
            return "p" in open_tags
        if tag == "li":
            if "li" not in open_tags:
                return False
            last_li = len(open_tags) - 1 - open_tags[::-1].index("li")
            list_indexes = [
                index for index, open_tag in enumerate(open_tags)
                if open_tag in ("ul", "ol")
            ]
            return not list_indexes or last_li > max(list_indexes)
        return False
    
def print_tree(node, indent = 0):
    print(" " * indent, node)
    for child in node.children:
        print_tree(child, indent + 2)
