"""Layout and painting for replaced form controls."""

from ..html.text import Text
from ..rendering.draw import DrawLine, DrawRect, DrawText
from ..rendering.font_utils import get_font
from .base import Layout

INPUT_WIDTH_PX = 200
"""Default width, in pixels, used for the supported form controls."""


class InputLayout(Layout):
    """Lay out and paint one simple editable form control.

    ``input`` controls display their ``value`` attribute, while ``button``
    controls display a single direct text child. Submission is handled by the
    owning tab when a button is clicked or Enter is pressed in an input.
    """

    def __init__(self, node, parent, previous):
        """Create a control layout using the node's computed font."""
        super().__init__(node, parent, previous)
        self.font = get_font(node)

    def layout(self):
        """Position the control after its preceding inline sibling."""
        self.width = INPUT_WIDTH_PX
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")
        
    def paint(self):
        """Return a background rectangle and the control's displayed text."""
        cmds = []
        bgcolor = self.node.style.get("background-color", "transparent")
        if bgcolor != "transparent":
            rect = DrawRect(self.self_rect(), bgcolor)
            cmds.append(rect)
        if self.node.tag == "input":
            text = self.node.attributes.get("value", "")
        elif self.node.tag == "button":
            if len(self.node.children) == 1 and isinstance(self.node.children[0], Text):
                text = self.node.children[0].text
            else:
                text = ""
        if self.node.is_focused:
            cx = self.x + self.font.measure(text)
            cmds.append(DrawLine(cx, self.y, cx, self.y + self.height, "black", 1))
        color = self.node.style.get("color", "black")
        cmds.append(DrawText(self.x, self.y, text, self.font, color))
        return cmds
