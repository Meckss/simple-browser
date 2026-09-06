class StyleState:

    def __init__(self):
        self.weight = "normal"
        self.slant = "roman"
        self.size = 16

    def enter(self, tag_name):
        actions = {
            "i": self.enable_italic,
            "b": self.enable_bold,
            "small": self.make_smaller,
            "big": self.make_larger,
        }
        action = actions.get(tag_name)
        if action:
            action()

    def exit(self, tag_name):
        actions = {
            "i": self.disable_italic,
            "b": self.disable_bold,
            "small": self.make_larger,
            "big": self.make_smaller,
        }
        action = actions.get(tag_name)
        if action:
            action()

    def key(self):
        return self.weight, self.slant, self.size

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
