import tkinter
import sys
import html
import re

from page import Page
WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
PARAGRAPH_STEP = 30
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
        self.text = ""
        self.scroll = 0
        
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
        
        return html.unescape(body)
    
    def resize(self, event):
        if not self.text or event.width <= 0:
            return
        
        self.display_list = layout(self.text, event.width)
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
        if not self.display_list:
            return 0
        
        last_y = self.display_list[-1][1]
        content_height = last_y + VSTEP
        canvas_height = self.canvas.winfo_height()
        
        return max(0, content_height - canvas_height)
    
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

        for x, y, c in self.display_list:
            if y > self.scroll + canvas_height: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x,y - self.scroll,text = c, anchor = "nw")
        self.update_scroll_bar()

    def load(self, url):
        
        url, body = load_page(url)
        
        if url.view_source:
            self.text = body
        else:
            self.text = self.strip_html(body)
            
        self.display_list = layout(self.text, self.canvas.winfo_width())
        self.draw()
        
        
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

def layout(text, width):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == '\n':
            cursor_y += PARAGRAPH_STEP
            cursor_x = HSTEP
            continue
        
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= width - HSTEP:
            cursor_y += VSTEP
            cursor_x = HSTEP
    return display_list
        
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python browser.py <url>")
        sys.exit(1)
    browser = Browser()
    browser.load(Page(sys.argv[1]))
    tkinter.mainloop()