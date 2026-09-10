"""Block and inline layout for parsed HTML documents."""

import re

from .font import Font
from .text import Text
from .element import Element
from .draw import DrawRect
from .draw import DrawText
from .layout_constants import BLOCK_ELEMENTS, HSTEP, PARAGRAPH_STEP, VSTEP
from .css_utils import css_size_to_px
    
class BlockLayout:
    """Lay out one block of the document tree and produce paint commands."""

    def __init__(self, node, parent, previous):
        """Create a layout object for ``node``."""
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None
        self.display_list = []
        self.cursor_x = 0
        self.cursor_y = 0
        self.fonts = {}
        self.line = []
        
    def layout_mode(self):
        """Return ``"block"`` or ``"inline"`` for this node's contents."""
        if isinstance(self.node, Text):
            return "inline"

        if any(
            isinstance(child, Element) and child.tag in BLOCK_ELEMENTS
            for child in self.node.children
        ):
            return "block"

        if self.node.children:
            return "inline"
        return "block"
        
    def layout(self):
        """Compute this object's position, dimensions, and child layouts."""
        styles = getattr(self.node, "style", {})
        self.x = self.parent.x
        self.y = (
            self.previous.y + self.previous.height 
            if self.previous is not None
            else self.parent.y
        )
        width = styles.get("width")
        self.width = (
            css_size_to_px(width, self.parent.width)
            if width
            else self.parent.width
        )
        
        height = styles.get("height")
        explicit_height = None
        if height:
            parent_height = self.parent.height
            reference = parent_height if height.strip().endswith("%") else None
            if reference is not None or not height.strip().endswith("%"):
                explicit_height = css_size_to_px(height, reference)
        
        mode = self.layout_mode()
        if mode == "block":
            self._layout_block_children()
        else:
            self._layout_inline_content()

        if explicit_height is not None:
            self.height = explicit_height

    def _layout_block_children(self):
        """Create and lay out this block's child layout objects in order."""
        previous = None
        for child in self.node.children:
            next_child = BlockLayout(child, self, previous)
            self.children.append(next_child)
            next_child.layout()
            previous = next_child
        self.height = sum(child.height for child in self.children)

    def _layout_inline_content(self):
        """Lay out inline descendants into lines and calculate total height."""
        self.process_tree(self.node)
        self.flush()
        self.height = self.cursor_y
            
    def paint(self):
        """Return drawing commands for this layout object and inline text."""
        cmds = []
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                cmds.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmds.append(DrawText(x, y, word, font, color))
        return cmds
            
    def process_tree(self, tree):
        """Traverse an inline subtree, applying tag and text layout behavior."""
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
        """Wrap a text node into words and append them to the current line."""
        content = re.sub(r"\s+", " ", text.text)

        for word in content.split():
            color = text.parent.style["color"]
            font = self.get_font(text.parent)
            word_width = font.measure(word)
            space_width = font.measure(" ")

            required_width = word_width
            if self.line:
                required_width += space_width

            if self.cursor_x + required_width > self.width - HSTEP:
                self.flush()

            self.line.append((self.cursor_x, word, font, color))
            self.cursor_x += word_width + space_width
                    
    def flush(self):
        """Place the current line in the display list and start a new line."""
        if not self.line: return
        metrics = [font.metrics() for x, word, font, color in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        
        baseline = self.cursor_y + 1.25 * max_ascent
        
        for rel_x, word, font, color in self.line:
            x = self.x + rel_x
            y = self.y + baseline - font.metrics("ascent")
            self.display_list.append((x,y,word,font,color))
        
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        
        self.cursor_x = 0
        self.line = []

    
    def enter_tag(self, tag):
        """Apply layout behavior that occurs when entering an element."""
        handler = {"br": self._enter_line_break}.get(tag.tag)
        if handler:
            handler()

    def _enter_line_break(self):
        """Finish the current line and advance by one line-height step."""
        self.flush()
        self.cursor_y += VSTEP

    def exit_tag(self, tag):
        """Apply layout behavior that occurs after an element's children."""
        handler = {"p": self._exit_paragraph}.get(tag.tag)
        if handler:
            handler()

    def _exit_paragraph(self):
        """Finish a paragraph and add the paragraph separation spacing."""
        self.flush()
        self.cursor_y += PARAGRAPH_STEP

    def get_font(self, node):
        """Return a cached font matching the node's computed text styles."""
        styles = getattr(node, "style", {})
        size = styles.get("font-size", "16px")
        size = int(round(css_size_to_px(size)))

        weight = styles.get("font-weight", "normal")
        slant = styles.get("font-style", "normal")
        if slant == "normal":
            slant = "roman"
            
        family = styles.get("font-family", "Times")

        key = (family, size, weight, slant)
        if key not in self.fonts:
            self.fonts[key] = Font(family, size, weight, slant)
        return self.fonts[key]
