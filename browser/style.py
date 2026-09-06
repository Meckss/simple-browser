class Style:
    def __init__(self):
        self.weight = "normal"
        self.slant = "roman"
        self.size = 16

    def apply(self, tag):
        styles = {
            "i": self.enable_italic,
            "/i": self.disable_italic,
            "b": self.enable_bold,
            "/b": self.disable_bold,
            "small": self.make_smaller,
            "/small": self.make_larger,
            "big": self.make_larger,
            "/big": self.make_smaller,
        }

        action = styles.get(tag.tag)

        if action:
            action()

    def enable_italic(self):
        self.slant = "italic"

    def disable_italic(self):
        self.slant = "roman"

    def enable_bold(self):
        self.weight = "bold"

    def disable_bold(self):
        self.weight = "normal"

    def make_smaller(self):
        self.size -= 2

    def make_larger(self):
        self.size += 2