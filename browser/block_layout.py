"""Block and inline layout for parsed HTML documents."""

import re

from .text import Text
from .element import Element
from .draw import DrawRect
from .layout_constants import HSTEP, PARAGRAPH_STEP, VSTEP
from .css_utils import css_size_to_px
from .font_utils import get_font
from .layout import Layout
from .line_layout import LineLayout
from .text_layout import TextLayout

def _is_auto(value):
    """Return whether a CSS value is the ``auto`` keyword."""
    return isinstance(value, str) and value.strip().lower() == "auto"


class BlockLayout(Layout):
    """Lay out one document node and produce its background paint commands.

    Block-level children are represented by nested :class:`BlockLayout`
    instances. Inline content is represented by :class:`LineLayout` and
    :class:`TextLayout` descendants.
    """

    def __init__(self, node, parent, previous):
        """Create a layout object for a node in document order.

        Args:
            node: The parsed element or text node being laid out.
            parent: The containing layout object.
            previous: The preceding sibling layout, if any.
        """
        super().__init__(node, parent, previous)
        self.cursor_x = 0
        
    def layout_mode(self):
        """Return the layout mode required by this node's children.

        A node containing a block-level child uses block layout; all other
        nodes with content use inline layout.
        """
        if isinstance(self.node, Text):
            return "inline"

        if any(
            isinstance(child, Element)
            and child.style.get("display") in ("block", "list-item", "table")
            for child in self.node.children
        ):
            return "block"

        if self.node.children:
            return "inline"
        return "block"
        
    def layout(self):
        """Compute position, dimensions, and descendants for this node.

        Hidden elements retain a zero-sized layout object so callers can use
        the same layout-tree traversal for all nodes.
        """
        if isinstance(self.node, Element) and self.node.style.get("display") == "none":
            self.x = self.parent.x
            self.y = self.parent.y
            self.width = self.parent.width
            self.height = 0
            return

        styles = getattr(self.node, "style", {})
        self.x = self.parent.x
        self.y = (
            self.previous.y + self.previous.height 
            if self.previous is not None
            else self.parent.y
        )
        width = styles.get("width")
        if not width or _is_auto(width):
            self.width = self.parent.width
        else:
            self.width = css_size_to_px(
                width, self._length_reference(width, self.parent.width)
            )
        
        height = styles.get("height")
        explicit_height = None
        if height and not _is_auto(height):
            reference = self._length_reference(height, self.parent.height)
            if reference is not None or not height.strip().endswith("%"):
                explicit_height = css_size_to_px(height, reference)
        
        mode = self.layout_mode()
        if mode == "block":
            self._layout_block_children()
        else:
            self.new_line()
            self.process_tree(self.node)
            for line in self.children:
                line.layout()

        if explicit_height is not None:
            self.height = explicit_height
        else:
            self.height = sum(
                child.height + getattr(child, "spacing_after", 0)
                for child in self.children
            )

    def _length_reference(self, value, percentage_reference):
        """Return the reference used to resolve a relative CSS length.

        ``em`` values use the current element's font size, percentages use
        ``percentage_reference``, and absolute values do not need a reference.
        """
        if not isinstance(value, str):
            return percentage_reference

        unit = value.strip().lower()
        if unit.endswith("em") and not unit.endswith("rem"):
            styles = getattr(self.node, "style", {})
            return css_size_to_px(styles.get("font-size", "16px"))
        if unit.endswith("%"):
            return percentage_reference
        return None

    def _layout_block_children(self):
        """Create and lay out visible block children in document order."""
        previous = None
        for child in self.node.children:
            if isinstance(child, Element) and child.style.get("display") == "none":
                continue
            next_child = BlockLayout(child, self, previous)
            self.children.append(next_child)
            next_child.layout()
            previous = next_child
        self.height = sum(child.height for child in self.children)

    def paint(self):
        """Return the background drawing commands for this layout object.

        Inline text is painted by descendant ``TextLayout`` objects during
        the normal recursive paint-tree traversal.
        """
        cmds = []
        if isinstance(self.node, Element):
            bgcolor = self.node.style.get("background-color", "transparent")
            if bgcolor != "transparent":
                x2, y2 = self.x + self.width, self.y + self.height
                cmds.append(DrawRect(self.x, self.y, x2, y2, bgcolor))

        return cmds
            
    def process_tree(self, tree):
        """Traverse an inline subtree and build its line layout objects.

        Args:
            tree: The element or text node currently being processed.
        """
        if isinstance(tree, Text):
            self.process_text(tree)
            return

        if not tree.is_rendered() or tree.style.get("display") == "none":
            return

        self.enter_tag(tree)
        for child in tree.children:
            self.process_tree(child)
        self.exit_tag(tree)
                
    def process_text(self, text_node):
        """Normalize, wrap, and append a text node's words to its lines.

        Each word receives the computed font and color of its containing
        element and becomes a ``TextLayout`` child of the current line.
        """
        content = re.sub(r"\s+", " ", text_node.text)

        for word in content.split():
            color = text_node.parent.style["color"]
            font = get_font(text_node.parent)
            word_width = font.measure(word)
            space_width = font.measure(" ")
            line = self.children[-1]
            required_width = word_width
            if line.children:
                required_width += space_width

            if line.children and self.cursor_x + required_width > self.width - HSTEP:
                self.new_line()
                line = self.children[-1]

            previous_word = line.children[-1] if line.children else None
            text = TextLayout(text_node, word, line, previous_word, font, color)
            line.children.append(text)

            self.cursor_x += word_width + space_width

    def new_line(self):
        """Start a new inline line unless the current line is already empty."""
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        if last_line is not None and not last_line.children:
            return
        new_line = LineLayout(self.node, self, last_line)
        self.children.append(new_line)
    
    def enter_tag(self, tag):
        """Apply layout behavior associated with entering an inline tag."""
        handler = {"br": self._enter_line_break}.get(tag.tag)
        if handler:
            handler()

    def _enter_line_break(self):
        """Add line-break spacing and begin a following inline line."""
        if self.children and self.children[-1].children:
            self.children[-1].spacing_after += VSTEP
        self.new_line()

    def exit_tag(self, tag):
        """Apply layout behavior associated with leaving an inline tag."""
        handler = {"p": self._exit_paragraph}.get(tag.tag)
        if handler:
            handler()

    def _exit_paragraph(self):
        """Add the configured separation after the current paragraph line."""
        if self.children and self.children[-1].children:
            self.children[-1].spacing_after += PARAGRAPH_STEP
