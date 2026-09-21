"""Tkinter user interface, browser chrome, and tab management.

The module owns the application window, shared viewport scrolling, tab
selection, navigation controls, and address-bar input. Individual tabs own
document loading, layout, and per-tab navigation history.
"""

import tkinter

from .tab import Tab
from .constants import HEIGHT, SCROLL_STEP, WIDTH
from ..rendering.font import Font
from ..rendering.draw import DrawLine, DrawOutline, Rect, DrawText, DrawRect

class Browser:
    """Manage browser tabs, the shared viewport, and user input.

    The canvas displays the active tab below the browser chrome. Scrolling is
    shared by the window, while navigation history remains local to each tab.
    """

    def __init__(self):
        """Create the browser window and install its event handlers."""
        self.tabs = []
        self.focus = None
        self.active_tab = None
        self.window = tkinter.Tk()
        self.chrome = Chrome(self)
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
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<BackSpace>", self.handle_backspace)

    def handle_down(self, e):
        """Handle a Down key event by scrolling one keyboard unit."""
        self.scroll_page(SCROLL_STEP)

    def handle_click(self, e):
        """Route a canvas click to page content or the browser chrome.

        Page coordinates are translated to account for the tab bar before
        the active tab receives the click.
        """
        if self.active_tab is None:
            return
        navigated = self.active_tab.click(
            e.x, e.y - self.chrome.bottom, self.scroll
        )
        if navigated:
            self.scroll = 0
        if e.y < self.chrome.bottom:
            self.focus = None
            self.chrome.click(e.x, e.y)
        else:
            self.focus = "content"
            self.chrome.blur()
        self.draw()
        
    def handle_key(self, e):
        """Route a printable character to the focused UI component."""
        if len(e.char) == 0:
            return
        if not (0x20 <= ord(e.char) < 0x7f):
            return
        if self.chrome.focus == "address bar":
            handled = self.chrome.keypress(e.char)
        elif self.focus == "content" and self.active_tab is not None:
            handled = self.active_tab.keypress(e.char)
        else:
            handled = False

        if handled:
            self.draw()
        
    def handle_enter(self, e):
        """Route Enter to the component that currently owns focus."""
        if self.chrome.focus == "address bar":
            handled = self.chrome.enter()
        else:
            handled = False

        if handled:
            self.draw()
    
    def handle_backspace(self, e):
        """Route Backspace to the component that currently owns focus."""
        if self.chrome.focus == "address bar":
            handled = self.chrome.backspace()
        elif self.focus == "content" and self.active_tab is not None:
            handled = self.active_tab.backspace()
        else:
            handled = False

        if handled:
            self.draw()

    def new_tab(self, url):
        """Create, load, and activate a tab for ``url``.

        The tab's layout viewport excludes the height occupied by the tab bar.
        """
        new_tab = Tab(HEIGHT - self.chrome.bottom)
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.scroll = 0
        self.draw()

    def resize(self, event):
        """Relayout the chrome and active tab after a canvas resize."""
        if event.width <= 0:
            return
        self.chrome.resize(event.width)
        if self.active_tab is None:
            return
        self.active_tab.resize(event.width)
        self.scroll = max(0, min(self.scroll, self.max_scroll()))
        self.draw()

    def scroll_page(self, amount):
        """Move the viewport by ``amount`` pixels and redraw the window.

        The resulting offset is clamped between the top and bottom of the
        active document.
        """
        self.scroll = max(0, min(self.scroll + amount, self.max_scroll()))
        self.draw()

    def mouse_scroll(self, event):
        """Translate a mouse-wheel event into a vertical scroll step."""
        self.scroll_page(-SCROLL_STEP if event.delta > 0 else SCROLL_STEP)

    def max_scroll(self):
        """Return the greatest valid document scroll offset in pixels."""
        if self.active_tab is None or self.active_tab.layout is None:
            return 0
        viewport_height = max(0, self.canvas.winfo_height() - self.chrome.bottom)
        return max(0, self.active_tab.layout.height - viewport_height)

    def update_scroll_bar(self):
        """Update the scrollbar thumb to match the current document offset."""
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
        """Apply a Tkinter scrollbar command and redraw the document.

        Tkinter supplies commands such as ``("moveto", fraction)`` and
        ``("scroll", amount, "units"|"pages")``.
        """
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
        """Redraw page content, the scrollbar, and the browser chrome."""
        self.canvas.delete("all")
        if self.active_tab is not None:
            if self.active_tab.fragment_scroll is not None:
                self.scroll = self.active_tab.fragment_scroll
                self.active_tab.fragment_scroll = None
            self.active_tab.draw(
                self.canvas, self.scroll - self.chrome.bottom
            )
        self.update_scroll_bar()
        for cmd in self.chrome.paint():
            cmd.execute(0, self.canvas)

class Chrome:
    """Render and manage tabs, navigation controls, and the address bar.

    The chrome contains controls for opening tabs, moving through the active
    tab's history, switching tabs, and entering URLs or search terms.
    """

    def __init__(self, browser):
        """Create browser chrome associated with ``browser``."""
        self.browser = browser
        self.width = WIDTH
        self.font = Font("Times", 20, "normal", "roman")
        self.font_height = self.font.metrics("linespace")
        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2*self.padding
        plus_width = self.font.measure("+") + 2*self.padding
        self.newtab_rect = Rect(
            self.padding, self.padding,
            self.padding + plus_width,
            self.padding + self.font_height
        )
        self.bottom = self.tabbar_bottom
        self.urlbar_top = self.tabbar_bottom
        self.urllbar_bottom = self.urlbar_top + self.font_height + 2 * self.padding
        self.bottom = self.urllbar_bottom
        back_width = self.font.measure("<") + 2 * self.padding
        self.back_rect = Rect(
            self.padding,
            self.urlbar_top + self.padding,
            self.padding + back_width,
            self.urllbar_bottom - self.padding
        )
        forward_width = self.font.measure(">") + 2 * self.padding
        self.forward_rect = Rect(
            self.back_rect.right + self.padding,
            self.urlbar_top + self.padding,
            self.back_rect.right + self.padding + forward_width,
            self.urllbar_bottom - self.padding
        )
        self.address_rect = Rect(
            self.forward_rect.right + self.padding,
            self.urlbar_top + self.padding,
            self.width - self.padding,
            self.urllbar_bottom - self.padding
        )
        self.focus = None
        self.address_bar = ""

    def resize(self, width):
        """Update chrome geometry after the canvas width changes."""
        if width <= 0 or width == self.width:
            return
        self.width = width
        self.address_rect.right = width - self.padding

    def blur(self):
        """Remove focus from the address bar."""
        self.focus = None

    def tab_rect(self, i):
        """Return the tab-bar rectangle for the tab at index ``i``.

        Args:
            i (int): Zero-based index of the tab.

        Returns:
            Rect: The tab's bounds in canvas coordinates.
        """
        tabs_start = self.newtab_rect.right + self.padding
        tab_width = self.font.measure("Tab X") + 2*self.padding
        return Rect(
            tabs_start + tab_width * i, self.tabbar_top,
            tabs_start + tab_width * (i + 1), self.tabbar_bottom
        )

    def click(self, x, y):
        """Handle a click on a tab-bar or address-bar control.

        Args:
            x (int): Horizontal canvas coordinate of the click.
            y (int): Vertical canvas coordinate of the click.
        """
        if self.newtab_rect.contains_point(x,y):
            self.browser.new_tab("https://browser.engineering")
        elif (self.back_rect.contains_point(x, y)
              and self.browser.active_tab.can_go_back()):
            self.browser.active_tab.go_back()
        elif (self.forward_rect.contains_point(x, y)
              and self.browser.active_tab.can_go_forward()):
            self.browser.active_tab.go_forward()
        elif self.address_rect.contains_point(x, y):
            self.focus = "address bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains_point(x,y):
                    self.browser.active_tab = tab
                    break
    
    def keypress(self, char):
        """Append ``char`` to the address bar when it has focus."""
        if self.focus == "address bar":
            self.address_bar += char
            return True
        return False
        
    def enter(self):
        """Submit the focused address bar as a URL or Google search.

        Fully qualified URLs and supported special schemes are loaded as-is.
        Bare hosts ending in ``.com``, ``.org``, or ``.engineering`` receive
        an ``https://`` prefix; other bare text becomes a Google search.
        """
        if self.focus == "address bar":
            url = self.address_bar.strip()
            if url and "://" not in url and not url.startswith(
                ("data:", "file:", "view-source:")
            ):
                hostname = url.split("/", 1)[0].lower()
                if hostname.endswith((".com", ".org", ".engineering")):
                    url = "https://" + url
                else:
                    query = ""
                    for byte in url.encode("utf-8"):
                        char = chr(byte)
                        if (char.isalnum() or char in "-_.~") and byte < 128:
                            query += char
                        elif byte == 0x20:
                            query += "+"
                        else:
                            query += "%{:02X}".format(byte)
                    url = "https://www.google.com/search?q=" + query
            if url:
                self.browser.active_tab.load(url)
            self.focus = None
            return True
        return False
    
    def backspace(self):
        """Remove the final address-bar character when it has focus."""
        if self.focus != "address bar":
            return False
        if len(self.address_bar) == 0:
            return False
        self.address_bar = self.address_bar[:-1]
        return True

    def paint(self):
        """Return drawing commands for the tabs and browser controls.

        Returns:
            list: Drawing commands that can be executed on the browser
                canvas.
        """
        cmds = []
        cmds.append(DrawRect(Rect(0, 0, self.width, self.bottom), "white"))
        cmds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmds.append(DrawText(
            self.newtab_rect.left + self.padding,
            self.newtab_rect.top,
            "+", self.font, "black"
        ))
        back_color = (
            "black" if self.browser.active_tab is not None
            and self.browser.active_tab.can_go_back() else "gray"
        )
        forward_color = (
            "black" if self.browser.active_tab is not None
            and self.browser.active_tab.can_go_forward() else "gray"
        )
        cmds.append(DrawOutline(self.back_rect, back_color, 1))
        cmds.append(DrawText(
            self.back_rect.left + self.padding,
            self.back_rect.top,
            "<", self.font, back_color
        ))
        cmds.append(DrawOutline(self.forward_rect, forward_color, 1))
        cmds.append(DrawText(
            self.forward_rect.left + self.padding,
            self.forward_rect.top,
            ">", self.font, forward_color
        ))
        cmds.append(DrawLine(
            0, self.bottom, self.width, self.bottom, "black", 1
        ))
        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)
            cmds.append(DrawLine(
                bounds.left, 0, bounds.left, bounds.bottom,
                "black", 1
            ))
            cmds.append(DrawLine(
                bounds.right, 0, bounds.right, bounds.bottom,
                "black", 1
            ))
            cmds.append(DrawText(
                bounds.left + self.padding, bounds.top + self.padding,
                "Tab {}".format(i), self.font, "black"
            ))
            if tab == self.browser.active_tab:
                cmds.append(DrawLine(
                    0, bounds.bottom, bounds.left, bounds.bottom,
                    "black", 1
                ))
                cmds.append(DrawLine(
                    bounds.right, bounds.bottom, self.width, bounds.bottom,
                    "black", 1
                ))
        cmds.append(DrawOutline(self.address_rect, "black", 1))
        url = str(self.browser.active_tab.page)     
        if self.focus == "address bar":
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                self.address_bar, self.font, "black"
            ))
            w = self.font.measure(self.address_bar)
            cmds.append(DrawLine(
                self.address_rect.left + self.padding + w,
                self.address_rect.top,
                self.address_rect.left + self.padding + w,
                self.address_rect.bottom,
                "red", 1
            ))
        else:
            cmds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                url, self.font, "black"
            ))

        return cmds
