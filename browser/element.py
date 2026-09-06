NON_RENDERING_TAGS = {"script", "style"}


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.parent = parent
        self.children = []

    def is_rendered(self):
        """Return whether this element participates in visual rendering."""
        return self.tag not in NON_RENDERING_TAGS
        
    def __repr__(self):
        return "<" + self.tag + ">"
