"""Tkinter user interface and document-loading orchestration."""

import tkinter
from pathlib import Path

from .page import Page
from .element import Element
from .text import Text
from .document_layout import DocumentLayout
from .html_parser import HTMLParser
from .style import style
from .css_parser import CSSParser
from .tree_utils import tree_to_list
from .selector import cascade_priority
from .ui_constants import HEIGHT, SCROLL_STEP, WIDTH
STYLE_SHEET_PATH = Path(__file__).with_name("browser.css")
DEFAULT_STYLE_SHEET = CSSParser(STYLE_SHEET_PATH.read_text(encoding="utf8")).parse()

class Browser:
    """Display parsed pages in a scrollable Tkinter window."""
    def __init__(self):
        """Create the window, canvas, scrollbar, and input bindings."""
        self.window = tkinter.Tk()
        self.page = None
        self.canvas = tkinter.Canvas(
            self.window,
            width = WIDTH,
            height = HEIGHT,
            bg = "pink"
        )
        self.canvas.pack(side = "left", fill = "both", expand = True)
        self.scroll_bar = tkinter.Scrollbar(
            self.window,
            orient="vertical",
            command = self.scroll_bar_scroll
        )
        self.scroll_bar.pack(side = "right", fill = "y")
        self.scroll = 0
        self.text = ""
        self.layout = None
        self._layout_width = None
        
        self.canvas.bind("<Configure>", self.resize)
        self.window.bind("<Down>", lambda e: self.scroll_page(SCROLL_STEP))
        self.window.bind("<Up>", lambda e: self.scroll_page(-SCROLL_STEP))

        self.window.bind("<MouseWheel>", self.mouse_scroll)

        self.window.bind("<Button-4>", lambda e: self.scroll_page(-SCROLL_STEP))
        self.window.bind("<Button-5>", lambda e: self.scroll_page(SCROLL_STEP))   
             
    def render_text(self, text, reset_scroll=True, page=None):
        """Render HTML text, optionally retaining the current scroll position."""
        self.text = text
        self.page = page

        width = self.canvas.winfo_width()
        if width <= 0:
            width = WIDTH

        self.make_layout(text, width, page)

        if reset_scroll:
            self.scroll = 0

        self.display_list = []
        paint_tree(self.layout, self.display_list)
        self.draw()

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
                try:
                    stylesheet = style_url.request()
                except OSError:
                    continue
                rules.extend(CSSParser(stylesheet).parse())

        style(root, sorted(rules, key = cascade_priority))
        self.layout = DocumentLayout(root, width)
        self.layout.layout()
    
    def resize(self, event):
        """Reflow the current document after the canvas is resized.

        Tk can report a configure event immediately after the first render;
        events for the current layout width are ignored to avoid duplicate
        parsing and layout work.
        """
        if event.width <= 0 or not self.text:
            return
        if event.width == self._layout_width:
            return
        self.make_layout(self.text, event.width, self.page)
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.display_list = []
        paint_tree(self.layout, self.display_list)
        self.draw()
        
    def scroll_page(self, amount):
        """Move the viewport by ``amount`` pixels and redraw it."""
        self.scroll += amount
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.draw()
    
    
    def mouse_scroll(self, event):
        """Translate a mouse-wheel event into a vertical scroll."""
        if event.delta > 0:
            self.scroll_page(-SCROLL_STEP)
        else:
            self.scroll_page(SCROLL_STEP)
        
    def max_scroll(self):
        """Return the greatest valid vertical scroll offset."""
        if self.layout is None:
            return 0
        
        canvas_height = self.canvas.winfo_height()
        
        return max(0, self.layout.height - canvas_height)
    
    def update_scroll_bar(self):
        """Update the scrollbar thumb to reflect the current viewport."""
        canvas_height = self.canvas.winfo_height()
        maximum = self.max_scroll()
        
        if maximum == 0:
            self.scroll_bar.set(0,1)
            return
        
        first = self.scroll / (maximum + canvas_height)
        last = (self.scroll + canvas_height) / (maximum + canvas_height)
        
        self.scroll_bar.set(first, last)
    
    def scroll_bar_scroll(self, *args):
        """Handle Tkinter scrollbar commands and redraw the document."""
        canvas_height = self.canvas.winfo_height()
        maximum = self.max_scroll()
        
        if args[0] == "moveto":
            self.scroll = float(args[1]) * (maximum + canvas_height)

        elif args[0] == "scroll":
            amount = int(args[1])

            if args[2] == "units":
                self.scroll += amount * SCROLL_STEP
            elif args[2] == "pages":
                self.scroll += amount * canvas_height

        self.scroll = max(0, min(self.scroll, maximum))
        self.draw()
        
    def draw(self):
        """Paint visible display commands onto the canvas."""
        self.canvas.delete("all")
        canvas_height = self.canvas.winfo_height()

        for cmd in self.display_list:
            if cmd.top > self.scroll + canvas_height: continue
            if cmd.bottom < self.scroll: continue
            cmd.execute(self.scroll, self.canvas)
        self.update_scroll_bar()
        
    def show_error(self, title, error):
        """Render a user-facing error page with the supplied message."""
        error_text = (
            f"{title}\n\n"
            f"{error}\n\n"
            "Usage:\n"
            "  python browser.py <url>\n\n"
            "Supported URLs:\n"
            "  http://example.com\n"
            "  https://example.com\n"
            "  file:///path/to/file\n"
            "  data:text/plain,Hello"
        )
        
        self.render_text(error_text)
    
    def load(self, url):
        """Fetch and render ``url``, showing supported load errors in the UI."""
        try:
            page, body = load_page(Page(url))
            self.render_text(body, page=page)
            
        except (OSError, ValueError, RuntimeError) as error:
            self.show_error("Unable to load page", str(error))
        
        
def load_page(page, max_redirects = 10):
    """Request a page and follow redirects up to ``max_redirects`` times.

    Returns:
        tuple[Page, str]: The final page object and its response body.

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
        
        page = Page(next_page)
    return page, body

def paint_tree(layout_object, display_list):
    """Append paint commands for a layout tree in pre-order."""
    display_list.extend(layout_object.paint())
    
    for child in layout_object.children:
        paint_tree(child, display_list)
