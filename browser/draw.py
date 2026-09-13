"""Drawing command objects consumed by the Tkinter canvas."""

class DrawText:
    """Represent one piece of text to draw at a document coordinate."""
    def __init__(self, x1, y1, text, font, color):
        """Create a text command with its font and foreground color."""
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + font.metrics("linespace")
    
    def execute(self, scroll, canvas):
        """Draw the text on ``canvas`` adjusted by the vertical scroll offset."""
        canvas.create_text(
            self.left, self.top - scroll,
            text = self.text,
            font = self.font.tk_font,
            anchor = "nw",
            fill = self.color
        )
    
class DrawRect:
    """Represent a filled rectangle to draw behind page content."""
    def __init__(self, rect, color):
        """Create a rectangle command from a :class:`Rect` and fill color."""
        self.rect = rect
        self.color = color

    def execute(self, scroll, canvas):
        """Draw the rectangle adjusted by the vertical scroll offset."""
        canvas.create_rectangle(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            width = 0,
            fill = self.color
        )

class DrawOutline:
    """Represent an unfilled rectangle outline."""

    def __init__(self, rect, color, thickness):
        """Create an outline command for ``rect``."""
        self.rect = rect
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        """Draw the outline adjusted by the vertical scroll offset."""
        canvas.create_rectangle(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            width = self.thickness,
            outline = self.color
        )

class DrawLine:
    """Represent a line segment drawing command."""

    def __init__(self, x1, y1, x2, y2, color, thickness):
        """Create a line command from two endpoints and its appearance."""
        self.rect = Rect(x1, y1, x2, y2)
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        """Draw the line adjusted by the vertical scroll offset."""
        canvas.create_line(
            self.rect.left, self.rect.top - scroll,
            self.rect.right, self.rect.bottom - scroll,
            fill = self.color, width = self.thickness
        )


class Rect:
    """Store rectangular bounds and provide point hit testing."""

    def __init__(self, left, top, right, bottom):
        """Create a rectangle from its left, top, right, and bottom edges."""
        self.left = left
        self.right = right
        self.bottom = bottom
        self.top = top

    def contains_point(self, x, y):
        """Return whether ``(x, y)`` lies inside the rectangle."""
        return x >= self.left and x < self.right \
            and y >= self.top and y < self.bottom
