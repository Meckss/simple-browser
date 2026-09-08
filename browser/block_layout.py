import re

from .font import FontCache
from .style_state import StyleState
from .text import Text
from .element import Element
from .draw import DrawRect
from .draw import DrawText

HSTEP, VSTEP = 13, 18
PARAGRAPH_STEP = 30
BLOCK_ELEMENTS = [
    "html", "body", "article", "section", "nav", "aside",
    "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
    "footer", "address", "p", "hr", "pre", "blockquote",
    "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
    "figcaption", "main", "div", "table", "form", "fieldset",
    "legend", "details", "summary"
]
    
class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.width = 0
        self.fonts = None
        self.style = None
        self.line =[]
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = []
        
    def layout_mode(self):
        if isinstance(self.node, Text):
            return "inline"
        if any([isinstance(child, Element) and \
                child.tag in BLOCK_ELEMENTS for child in self.node.children]):
            return "block"
        if self.node.children:
            return "inline"
        return "block"
        
    def layout(self):
        self.x = self.parent.x
        self.width = self.parent.width
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y
        mode = self.layout_mode()
        if mode == "block":
            previous = None
            for child in self.node.children:
                next_child = BlockLayout(child, self, previous)
                self.children.append(next_child)
                next_child.layout()
                previous = next_child
            self.height = sum([child.height for child in self.children])

        else: 
            self.cursor_x = 0
            self.cursor_y = 0
            self.fonts = FontCache()
            self.style = StyleState()
            self.line =[]
            
            self.process_tree(self.node)
                
            self.flush()
            self.height = self.cursor_y
            
    def paint(self):
        cmds = []
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                cmds.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                cmds.append(DrawText(x, y, word, font))
        return cmds
            
    def process_tree(self, tree):
        if isinstance(tree, Text):
            self.process_text(tree)
            return

        if not tree.is_rendered():
            return

        self.enter_tag(tree)
        for child in tree.children:
            self.process_tree(child)
        self.exit_tag(tree)
                
    def process_text(self, text):
        content = re.sub(r"\s+", " ", text.text)

        for word in content.split():
            font = self.get_font()
            word_width = font.measure(word)
            space_width = font.measure(" ")

            required_width = word_width
            if self.line:
                required_width += space_width

            if self.cursor_x + required_width > self.width - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font))
            self.cursor_x += word_width + space_width
                    
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for rel_x, word, font in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x,y,word,font))
        
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        
        self.cursor_x = 0
        self.line = []

    
    def enter_tag(self, tag):
        self.style.enter(tag.tag)

        if tag.tag == "br":
            self.flush()
            self.cursor_y += VSTEP

    def exit_tag(self, tag):
        self.style.exit(tag.tag)

        if tag.tag == "p":
            self.flush()
            self.cursor_y += PARAGRAPH_STEP
    
    def get_font(self):
        return self.fonts.get(self.style)
