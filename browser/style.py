class Style:
    def __init__(self):
        self.weight = "normal"
        self.slant = "roman"

    def apply(self, tag):
        if tag.tag == "i":
            self.slant = "italic"
        elif tag.tag == "/i":
            self.slant = "roman"
        elif tag.tag == "b":
            self.weight = "bold"
        elif tag.tag == "/b":
            self.weight = "normal"