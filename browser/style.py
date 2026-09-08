from .css_parser import CSSParser
from .element import Element

INHERITED_PROPERTIES = {
    "font-size" : "16px",
    "font-style": "normal",
    "font-weight": "normal",
    "color": "black"
}

def style(node, rules):
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
    for prop, default_value in INHERITED_PROPERTIES.items():
        if node.parent and hasattr(node.parent, "style"):
            node.style[prop] = node.parent.style.get(prop, default_value)
        else:
            node.style[prop] = default_value

    for selector, body in rules:
        if not selector.matches(node):
            continue
        for prop, value in body.items():
            node.style[prop] = value

    if "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for prop, value in pairs.items():
            node.style[prop] = value

    if node.style["font-size"].endswith("%"):
        if node.parent and hasattr(node.parent, "style"):
            parent_font_size = node.parent.style["font-size"]
        else:
            parent_font_size = INHERITED_PROPERTIES["font-size"]
        node_pct = float(node.style["font-size"][:-1]) / 100
        parent_px = float(parent_font_size[:-2])
        node.style["font-size"] = str(node_pct * parent_px) + "px"
    for child in node.children:
        style(child, rules)

            
