"""Font wrapper used by text measurement and drawing."""

import tkinter.font


class Font:
    """Wrap a Tk font and expose the measurements needed by layout."""

    def __init__(self, family, size, weight, slant):
        """Create a font with a point size, weight, and slant."""
        self._font = tkinter.font.Font(
            family=family,
            size=size,
            weight=weight,
            slant=slant,
        )
        self._measure_cache = {}
        self._metrics_cache = {}

    def measure(self, text):
        """Return the rendered width of ``text`` in pixels, using a cache."""
        if text not in self._measure_cache:
            self._measure_cache[text] = self._font.measure(text)
        return self._measure_cache[text]

    def metrics(self, option=None):
        """Return Tk font metrics, caching each requested option."""
        if option not in self._metrics_cache:
            if option is None:
                self._metrics_cache[option] = self._font.metrics()
            else:
                self._metrics_cache[option] = self._font.metrics(option)
        return self._metrics_cache[option]

    @property
    def tk_font(self):
        """Return the underlying Tk font instance."""
        return self._font
    
