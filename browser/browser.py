import tkinter
import re

from .page import Page
from .layout import Layout
from .html_parser import HTMLParser

WIDTH, HEIGHT = 800, 600
SCROLL_STEP = 100
HSTEP, VSTEP = 13, 18

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width = WIDTH,
            height = HEIGHT
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
        
        self.canvas.bind("<Configure>", self.resize)
        self.window.bind("<Down>", lambda e: self.scroll_page(SCROLL_STEP))
        self.window.bind("<Up>", lambda e: self.scroll_page(-SCROLL_STEP))

        self.window.bind("<MouseWheel>", self.mouse_scroll)

        self.window.bind("<Button-4>", lambda e: self.scroll_page(-SCROLL_STEP))
        self.window.bind("<Button-5>", lambda e: self.scroll_page(SCROLL_STEP))   
             
    def render_text(self, text, reset_scroll=True):
        self.text = text

        width = self.canvas.winfo_width()
        if width <= 0:
            width = WIDTH

        self.make_layout(text, width)

        if reset_scroll:
            self.scroll = 0

        self.draw()

    def make_layout(self, body, width):
        tree = HTMLParser(body).parse_html()
        self.layout = Layout(tree, width)
    
    def resize(self, event):
        if event.width <= 0 or not self.text:
            return
        self.make_layout(self.text, event.width)
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.draw()
        
    def scroll_page(self, amount):
        self.scroll += amount
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.draw()
    
    
    def mouse_scroll(self, event):
        if event.delta > 0:
            self.scroll_page(-SCROLL_STEP)
        else:
            self.scroll_page(SCROLL_STEP)
        
    def max_scroll(self):
        if self.layout is None:
            return 0
        
        canvas_height = self.canvas.winfo_height()
        
        return max(0, self.layout.content_height - canvas_height)
    
    def update_scroll_bar(self):
        canvas_height = self.canvas.winfo_height()
        maximum = self.max_scroll()
        
        if maximum == 0:
            self.scroll_bar.set(0,1)
            return
        
        first = self.scroll / (maximum + canvas_height)
        last = (self.scroll + canvas_height) / (maximum + canvas_height)
        
        self.scroll_bar.set(first, last)
    
    def scroll_bar_scroll(self, *args):
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
        self.canvas.delete("all")
        canvas_height = self.canvas.winfo_height()

        for x, y, c, f in self.layout.display_list:
            if y > self.scroll + canvas_height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x,y - self.scroll,text = c, anchor = "nw", font=f.tk_font)
        self.update_scroll_bar()
        
    def show_error(self, title, error):
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
        try:
            __, body = load_page(Page(url))
            self.render_text(body)
            
        except (OSError, ValueError, RuntimeError) as error:
            self.show_error("Unable to load page", str(error))
        
        
def load_page(page, max_redirects = 10):
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
