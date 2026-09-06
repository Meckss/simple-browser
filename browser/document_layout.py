from .block_layout import BlockLayout

HSTEP, VSTEP = 13, 18

class DocumentLayout:
    def __init__(self, node, width):
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = width
        self.height = None
        
    def layout(self):
        child = BlockLayout(self.node, self ,None)
        self.children.append(child)
        
        
        self.width = self.width - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.height = child.height
        
    def paint(self):
        return []