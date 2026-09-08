from .css_parser import CSSParser
from .element import Element

def style(node):
    """
    Apply inline CSS styles to a HTML node and its descendents

    Each node receives a ``style`` dictionary. If an element has a
    ``style`` attribute, its CSS declarations are parsed and stored in
    that dictionary.
    
    Args:
        node: The HTML element or its descendents
    """
    if not isinstance(node, Element):
        return

    node.style = {}
    if "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for prop, value in pairs.items():
            node.style[prop] = value
    for child in node.children:
        style(child)
