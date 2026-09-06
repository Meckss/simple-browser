from .block_layout import BlockLayout

HSTEP, VSTEP = 13, 18
WIDTH = 800

class DocumentLayout:
    def __init__(self, node, width):
        self.node = node
        self.parent = None
        self.children = []
        self.x = None
        self.y = None
        self.width = width
        self.height = None
        self.display_list = []
        
    def layout(self):
        child = BlockLayout(self.node, self ,None)
        self.children.append(child)
        
        
        self.width = self.width - 2*HSTEP
        self.x = HSTEP
        self.y = VSTEP
        child.layout()
        self.display_list = child.display_list
        self.height = child.height