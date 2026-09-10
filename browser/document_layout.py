"""Top-level layout wrapper for an HTML document."""

from .block_layout import BlockLayout

HSTEP, VSTEP = 13, 18

class DocumentLayout:
    """Provide the viewport-relative root layout around the document body."""

    def __init__(self, node, width):
        """Create a document layout for ``node`` and an available width."""
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = width
        self.height = None
        
    def layout(self):
        """Lay out the document with horizontal and vertical page margins."""
        child = BlockLayout(self.node, self ,None)
        self.children.append(child)
        
        
        self.width = self.width - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height
        
    def paint(self):
        """Return document-level paint commands; children paint the content."""
        return []
