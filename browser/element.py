class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.parent = parent
        self.children = []
        
    def __repr__(self):
        return "<" + self.tag + ">"