"""Tkinter user interface and tab management for the browser."""

import tkinter

from .tab import Tab
from .ui_constants import HEIGHT, SCROLL_STEP, WIDTH

class Browser:
    """Manage browser tabs, the shared viewport, and user input."""

    def __init__(self):
        """Create the browser window and install its event handlers."""
        self.tabs = []
        self.active_tab = None
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(self.window, width=WIDTH, height=HEIGHT,
                                     bg="pink")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_bar = tkinter.Scrollbar(
            self.window, orient="vertical", command=self.scroll_bar_scroll
        )
        self.scroll_bar.pack(side="right", fill="y")
        self.scroll = 0
        self.canvas.bind("<Configure>", self.resize)
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", lambda e: self.scroll_page(-SCROLL_STEP))
        self.window.bind("<MouseWheel>", self.mouse_scroll)
        self.window.bind("<Button-4>", lambda e: self.scroll_page(-SCROLL_STEP))
        self.window.bind("<Button-5>", lambda e: self.scroll_page(SCROLL_STEP))
        self.window.bind("<Button-1>", self.handle_click)

    def handle_down(self, e):
        """Scroll the active document down by one keyboard unit."""
        self.scroll_page(SCROLL_STEP)

    def handle_click(self, e):
        """Forward a canvas click to the active tab and redraw the page."""
        navigated = self.active_tab.click(e.x, e.y, self.scroll)
        if navigated:
            self.scroll = 0
        self.draw()

    def new_tab(self, url):
        """Create, load, and activate a tab for ``url``."""
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.scroll = 0
        self.draw()

    def resize(self, event):
        """Relayout the active tab when the viewport width changes."""
        if self.active_tab is None or event.width <= 0:
            return
        self.active_tab.resize(event.width)
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.draw()

    def scroll_page(self, amount):
        """Move the viewport by ``amount`` pixels, within valid bounds."""
        self.scroll = max(0, min(self.scroll + amount, self.max_scroll()))
        self.draw()

    def mouse_scroll(self, event):
        """Translate a mouse-wheel event into a vertical scroll."""
        self.scroll_page(-SCROLL_STEP if event.delta > 0 else SCROLL_STEP)

    def max_scroll(self):
        """Return the greatest valid scroll offset for the active tab."""
        if self.active_tab is None or self.active_tab.layout is None:
            return 0
        return max(0, self.active_tab.layout.height - self.canvas.winfo_height())

    def update_scroll_bar(self):
        """Update the scrollbar thumb to match the current viewport."""
        canvas_height = self.canvas.winfo_height()
        maximum = self.max_scroll()
        if maximum == 0:
            self.scroll_bar.set(0, 1)
            return
        self.scroll_bar.set(
            self.scroll / (maximum + canvas_height),
            (self.scroll + canvas_height) / (maximum + canvas_height),
        )

    def scroll_bar_scroll(self, *args):
        """Apply a Tkinter scrollbar command and redraw the document."""
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
        """Draw the active tab at the browser's current scroll offset."""
        self.canvas.delete("all")
        if self.active_tab is None:
            return
        self.active_tab.draw(self.canvas, self.scroll)
        self.update_scroll_bar()
