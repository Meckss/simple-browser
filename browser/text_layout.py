"""Word-level layout and painting for inline text."""

from .draw import DrawText
from .layout import Layout


class TextLayout(Layout):
    """Lay out and paint one word in an inline line box."""

    def __init__(self, node, word, parent, previous, font, color):
        """Create a layout object for one rendered word.

        Args:
            node: The source text node containing the word.
            word: The normalized word to measure and paint.
            parent: The containing :class:`LineLayout`.
            previous: The preceding word on the line, if any.
            font: The computed font used to measure and draw the word.
            color: The computed text color.
        """
        super().__init__(node, parent, previous)
        self.word = word
        self.font = font
        self.color = color

    def layout(self):
        """Measure and position the word relative to its preceding word."""
        self.width = self.font.measure(self.word)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + self.previous.width + space
        else:
            self.x = self.parent.x
        self.height = self.font.metrics("linespace")

    def paint(self):
        """Return the drawing command for this word."""
        return [DrawText(self.x, self.y, self.word, self.font, self.color)]
