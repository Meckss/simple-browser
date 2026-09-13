"""Common base class for objects in the document layout tree."""

from .draw import Rect

class Layout:
    """Store the structure and geometry shared by every layout object."""

    def __init__(self, node, parent=None, previous=None):
        """Create a layout object in document order.

        Args:
            node: The parsed node represented by this layout object.
            parent: The containing layout object, if any.
            previous: The preceding sibling layout object, if any.
        """
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def layout(self):
        """Compute this object's geometry and the geometry of its children."""
        raise NotImplementedError

    def paint(self):
        """Return drawing commands emitted by this layout object."""
        return []

    def self_rect(self):
        """Return this layout object's bounds as a :class:`Rect`."""
        return Rect(self.x, self.y,
                    self.x + self.width, self.y + self.height)
