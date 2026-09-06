import tkinter
import tkinter.font
import sys
import html
import re

from tag import Tag
from text import Text
from page import Page
from layout import Layout

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
        self.display_list = []
        self.scroll = 0
        self.text = ""
        self.layout = None
        
        self.canvas.bind("<Configure>", self.resize)
        self.window.bind("<Down>", lambda e: self.scroll_page(SCROLL_STEP))
        self.window.bind("<Up>", lambda e: self.scroll_page(-SCROLL_STEP))

        self.window.bind("<MouseWheel>", self.mouse_scroll)

        self.window.bind("<Button-4>", lambda e: self.scroll_page(-SCROLL_STEP))
        self.window.bind("<Button-5>", lambda e: self.scroll_page(SCROLL_STEP))   
             
    def strip_html(self, body):
        body = re.sub(
            r"<(script|style).*?>.*?</\1>",
            "",
            body,
            flags=re.DOTALL | re.IGNORECASE
        )
        body = re.sub(r"<[^>]*>", "", body)
        body =  html.unescape(body)
        body = re.sub(r"\n\s*\n+", "\n\n", body)
        return body

    def make_layout(self, body, width):
        tokens = process_body(body)
        self.layout = Layout(tokens, width)
    
    def resize(self, event):
        if event.width <= 0:
            return
        self.make_layout(self.text, event.width)
        self.display_list = self.layout.display_list
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
        if not hasattr(self, "layout"):
            return 0
        
        canvas_height = self.canvas.winfo_height()
        
        return max(0, self.layout.content_height - canvas_height)
    
    def update_scroll_bar(self):
        maximum = self.max_scroll()
        
        if maximum == 0:
            self.scroll_bar.set(0,1)
        else:
            first = self.scroll / (maximum + HEIGHT)
            last = (self.scroll + HEIGHT) / (maximum + HEIGHT)
            self.scroll_bar.set(first, last)
    
    def scroll_bar_scroll(self, *args):
        maximum = self.max_scroll()
        
        if args[0] == "moveto":
            self.scroll = float(args[1]) * (maximum + HEIGHT)

        elif args[0] == "scroll":
            amount = int(args[1])

            if args[2] == "units":
                self.scroll += amount * SCROLL_STEP
            elif args[2] == "pages":
                self.scroll += amount * HEIGHT

        self.scroll = max(0, min(self.scroll, maximum))
        self.draw()
        
    def draw(self):
        self.canvas.delete("all")
        canvas_height = self.canvas.winfo_height()

        for x, y, c, f in self.display_list:
            if y > self.scroll + canvas_height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x,y - self.scroll,text = c, anchor = "nw", font=f)
        self.update_scroll_bar()
        
    def show_error(self, title, error):
        self.text = (
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

        width = self.canvas.winfo_width()
        if width <= 0:
            width = WIDTH

        self.make_layout(self.text, width)
        self.display_list = self.layout.display_list
        self.scroll = 0
        self.draw()
    
    def load(self, url):
        try:
            url, body = load_page(Page(url))

            self.text = body
            
            width = self.canvas.winfo_width()
            if width <= 0:
                width = WIDTH

            self.make_layout(body,width)
            self.display_list = self.layout.display_list
            self.scroll = 0
            self.draw()

        except Exception as error:
            self.show_error("Unable to load page", str(error))
        
        
def load_page(url, max_redirects = 10):
    redirects_followed = 0
    while True:
        body = url.request()
        
        if url.redirect_url is None:
            break
        
        if redirects_followed >= max_redirects:
            raise RuntimeError(
                f"too many redirects, limit is {max_redirects}"
            )
        
        redirects_followed += 1
        next_url = url.redirect_url
        
        if url.view_source and not next_url.startswith("view-source:"):
            next_url = "view-source:" + next_url
        
        url = Page(next_url)
    return url, body

def process_body(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer: 
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else: 
            buffer += c
    
    if not in_tag and buffer:
        out.append(Text(buffer))
    
    return out
        
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browser.py <url>")
        sys.exit(1)
    browser = Browser()
    browser.load(sys.argv[1])
    tkinter.mainloop()