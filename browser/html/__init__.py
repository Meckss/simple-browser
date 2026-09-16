"""HTML document structures and parsing."""

from .element import Element
from .parser import HTMLParser
from .text import Text

__all__ = ["Element", "HTMLParser", "Text"]
