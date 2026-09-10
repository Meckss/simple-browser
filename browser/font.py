"""Font wrapper used by text measurement and drawing."""

import tkinter.font


class Font:
    """Wrap a Tk font and expose the measurements needed by layout."""

    def __init__(self, size, weight, slant):
        """Create a font with a point size, weight, and slant."""
        self._font = tkinter.font.Font(
            size=size,
            weight=weight,
            slant=slant,
        )

    def measure(self, text):
        """Return the rendered width of ``text`` in pixels."""
        return self._font.measure(text)

    def metrics(self, option=None):
        """Return all Tk font metrics or one named metric."""
        if option is None:
            return self._font.metrics()
        return self._font.metrics(option)

    @property
    def tk_font(self):
        """Return the underlying Tk font instance."""
        return self._font
    
