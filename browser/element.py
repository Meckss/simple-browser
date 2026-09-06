NON_RENDERING_TAGS = {"script", "style"}


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.parent = parent
        self.children = []

    def is_rendered(self):
        return self.tag not in NON_RENDERING_TAGS
        
    def __repr__(self):
        return "<" + self.tag + ">"
