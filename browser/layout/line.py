"""Inline line-box layout for a block's text content."""

from .base import Layout


class LineLayout(Layout):
    """Lay out one horizontal line of word-level text objects."""

    def __init__(self, node, parent, previous):
        """Create a line associated with an inline block.

        Args:
            node: The parsed node containing the inline content.
            parent: The containing :class:`BlockLayout`.
            previous: The preceding line, if this is not the first line.
        """
        super().__init__(node, parent, previous)
        self.spacing_after = 0
        
    def layout(self):
        """Position the line and vertically align all of its words."""
        self.width = self.parent.width
        self.x = self.parent.x
        
        if self.previous:
            self.y = self.previous.y + self.previous.height + self.previous.spacing_after
        else:
            self.y = self.parent.y
        
        for word in self.children:
            word.layout()
            
        if not self.children:
            self.height = 0
            return

        max_ascent = max(word.font.metrics("ascent") for word in self.children)
        baseline = self.y + 1.25 * max_ascent
        for word in self.children:
            word.y = baseline - word.font.metrics("ascent")
        max_descent = max(word.font.metrics("descent") for word in self.children)
        
        self.height = 1.25 * (max_ascent + max_descent)
        
    def paint(self):
        """Return no commands; child words paint themselves."""
        return []
        
        
