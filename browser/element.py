"""HTML element nodes used by parsing, styling, and layout."""

NON_RENDERING_TAGS = {"script", "style"}


class Element:
    """Represent an HTML element and its relationship to the document tree."""
    def __init__(self, tag, attributes, parent):
        """Create an element with its tag, attributes, and parent."""
        self.tag = tag
        self.attributes = attributes
        self.parent = parent
        self.children = []

    def is_rendered(self):
        """Return whether this element's contents participate in rendering."""
        return self.tag not in NON_RENDERING_TAGS
        
    def __repr__(self):
        """Return a compact representation containing the element tag."""
        return "<" + self.tag + ">"
