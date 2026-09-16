"""Text nodes in the parsed HTML tree."""

class Text:
    """Represent character data and its containing element."""
    def __init__(self, text, parent):
        """Create a text node with its source text and parent element."""
        self.text = text
        self.parent = parent
        self.children = []
        
    def __repr__(self):
        """Return the node's text using its normal string representation."""
        return repr(self.text)
        
