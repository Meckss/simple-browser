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
        self.canvas.pack()
        self.display_list = []
        self.scroll = 0
        
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
    
    def scroll_page(self, amount):
        self.scroll += amount
        self.scroll = max(0, self.scroll)
        
        self.draw()
    
    
    def mouse_scroll(self, event):
        if event.delta > 0:
            self.scroll_page(-SCROLL_STEP)
        else:
            self.scroll_page(SCROLL_STEP)
        
    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x,y - self.scroll,text = c)

    def load(self, url, max_redirects = 10):
        
        url, body = load_page(url)
        
        if url.view_source:
            display_text = body
        else:
            display_text = self.strip_html(body)
            
        self.display_list = layout(display_text)
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

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        if c == '\n':
            cursor_y += PARAGRAPH_STEP
            cursor_x = HSTEP
            continue
        
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP:
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