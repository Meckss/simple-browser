import tkinter.font


class Font:

    def __init__(self, size, weight, slant):
        self._font = tkinter.font.Font(
            size=size,
            weight=weight,
            slant=slant,
        )

    def measure(self, text):
        return self._font.measure(text)

    def metrics(self, option=None):
        if option is None:
            return self._font.metrics()
        return self._font.metrics(option)

    @property
    def tk_font(self):
        return self._font
    
