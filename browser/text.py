class Text:
    def __init__(self, text, parent):
        self.text = text
        self.parent = parent
        self.children = []
        
    def __repr__(self):
        return repr(self.text)
        
