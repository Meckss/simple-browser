"""Document loading, styling, layout, and hit testing for a browser tab."""

from pathlib import Path
import urllib.parse

from ..networking.webresource import WebResource
from ..html.element import Element
from ..html.text import Text
from ..layout.document import DocumentLayout
from ..html.parser import HTMLParser
from ..css.style import style
from ..css.parser import CSSParser
from ..html.tree_utils import tree_to_list
from ..css.selector import cascade_priority
from .constants import WIDTH
STYLE_SHEET_PATH = Path(__file__).parents[1] / "browser.css"
DEFAULT_STYLE_SHEET = CSSParser(STYLE_SHEET_PATH.read_text(encoding="utf8")).parse()
STYLESHEET_CACHE = {}

class Tab:
    """Own the document displayed in one browser tab."""
    def __init__(self, tab_height):
        """Create an empty tab with a content viewport ``tab_height`` high."""
        self.page = None
        self.text = ""
        self.layout = None
        self._layout_width = None
        self.tab_height = tab_height
        self.history = []
        self.forward_history = []
        self.fragment_scroll = None

    def render_text(self, text, page=None):
        """Parse and lay out HTML text."""
        self.text = text
        self.page = page

        self.make_layout(text, self._layout_width or WIDTH, page)
        self.display_list = []
        paint_tree(self.layout, self.display_list)
        self.fragment_scroll = self._fragment_scroll(page)

    def _fragment_scroll(self, page):
        """Return the document y-coordinate targeted by ``page.fragment``."""
        if page is None or page.fragment is None:
            return None

        target = urllib.parse.unquote(page.fragment)
        for layout_object in tree_to_list(self.layout, []):
            node = layout_object.node
            if not isinstance(node, Element):
                continue
            if (node.attributes.get("id") == target or
                    node.attributes.get("name") == target):
                return max(0, layout_object.y - self.layout.y)
        return None

    def make_layout(self, body, width, page = None):
        """Parse, style, and lay out a document for the viewport width.

        Recording ``width`` lets :meth:`resize` ignore duplicate configure
        events that do not require reflow.
        """
        self._layout_width = width
        root = HTMLParser(body).parse_html()
        rules = DEFAULT_STYLE_SHEET.copy()

        for node in tree_to_list(root, []):
            if not isinstance(node, Element):
                continue
            if node.tag == "style":
                stylesheet = "".join(
                    child.text for child in node.children
                    if isinstance(child, Text)
                )
                rules.extend(CSSParser(stylesheet).parse())
            elif (
                node.tag == "link"
                and node.attributes.get("rel") == "stylesheet"
                and "href" in node.attributes
                and page is not None
            ):
                style_url = page.resolve(node.attributes["href"])
                cache_key = str(style_url)
                try:
                    stylesheet_rules = STYLESHEET_CACHE.get(cache_key)
                    if stylesheet_rules is None:
                        stylesheet = style_url.request()
                        stylesheet_rules = CSSParser(stylesheet).parse()
                        STYLESHEET_CACHE[cache_key] = stylesheet_rules
                except OSError:
                    continue
                rules.extend(stylesheet_rules)

        style(root, sorted(rules, key = cascade_priority))
        self.layout = DocumentLayout(root, width)
        self.layout.layout()
    
    def resize(self, width):
        """Reflow the current document after the viewport is resized.

        Repeated resize notifications for the current layout width are
        ignored to avoid duplicate parsing and layout work.
        """
        if width <= 0 or not self.text or width == self._layout_width:
            return
        self.make_layout(self.text, width, self.page)
        self.display_list = []
        paint_tree(self.layout, self.display_list)

    def click(self, x, y, scroll=0):
        """Follow a link hit at viewport coordinates ``x``, ``y``.

        Returns:
            bool: Whether the click navigated to another URL.
        """
        y += scroll
        objs = [obj for obj in tree_to_list(self.layout, [])
                if obj.x <= x < obj.x + obj.width
                and obj.y <= y < obj.y + obj.height]
        if not objs: return
        elt = objs[-1].node
        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = self.page.resolve(elt.attributes["href"])
                self.load(url.original_url)
                return True
            elt = elt.parent
        return False
        
    def draw(self, canvas, scroll=0):
        """Paint visible display commands onto ``canvas``."""
        canvas_height = canvas.winfo_height()

        for cmd in self.display_list:
            if cmd.top > scroll + canvas_height: continue
            if cmd.bottom < scroll: continue
            cmd.execute(scroll, canvas)

    def go_back(self):
        """Return to the previous page in this tab's navigation history."""
        if len(self.history) > 1:
            self.forward_history.append(self.history.pop())
            self._load(self.history[-1], record_history=False)

    def can_go_back(self):
        """Return whether this tab has a page available in its back history."""
        return len(self.history) > 1

    def go_forward(self):
        """Return to the next page after navigating back in this tab."""
        if self.forward_history:
            url = self.forward_history.pop()
            self.history.append(url)
            self._load(url, record_history=False)

    def can_go_forward(self):
        """Return whether this tab has a page available in its forward history."""
        return bool(self.forward_history)

    def show_error(self, title, error):
        """Render a user-facing error page with the supplied message."""
        error_text = (
            f"{title}\n\n"
            f"{error}\n\n"
            "Usage:\n"
            "  python main.py <url>\n\n"
            "Supported URLs:\n"
            "  http://example.com\n"
            "  https://example.com\n"
            "  file:///path/to/file\n"
            "  data:text/plain,Hello"
        )
        
        self.render_text(error_text)
    
    def load(self, url):
        """Fetch and render ``url``, showing supported load errors in the UI."""
        self._load(url, record_history=True)

    def _load(self, url, record_history):
        """Fetch and render a URL, optionally recording a new navigation."""
        try:
            requested_page = WebResource(url)

            if record_history:
                self.history.append(url)
                self.forward_history.clear()

            if (self.page is not None and requested_page.fragment is not None
                    and requested_page.original_url.split("#", 1)[0] ==
                    self.page.original_url.split("#", 1)[0]):
                self.page = requested_page
                self.fragment_scroll = self._fragment_scroll(requested_page)
                return

            page, body = load_page(requested_page)
            self.render_text(body, page=page)
            
        except (OSError, ValueError, RuntimeError) as error:
            self.show_error("Unable to load page", str(error))
        
        
def load_page(page, max_redirects = 10):
    """Request a page and follow redirects up to ``max_redirects`` times.

    Returns:
        tuple[WebResource, str]: The final resource and its response body.

    Raises:
        RuntimeError: If the redirect limit is exceeded.
    """
    redirects_followed = 0
    while True:
        body = page.request()
        
        if page.redirect_url is None:
            break
        
        if redirects_followed >= max_redirects:
            raise RuntimeError(
                f"too many redirects, limit is {max_redirects}"
            )
        
        redirects_followed += 1
        next_page = page.redirect_url
        
        if page.view_source and not next_page.startswith("view-source:"):
            next_page = "view-source:" + next_page
        
        page = WebResource(next_page)
    return page, body

def paint_tree(layout_object, display_list):
    """Append paint commands for a layout tree in pre-order."""
    display_list.extend(layout_object.paint())
    
    for child in layout_object.children:
        paint_tree(child, display_list)
