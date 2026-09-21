# Simple Browser

A from-scratch graphical web browser built in Python. It implements the core
pieces of a browser engine—networking, URL handling, HTML parsing, CSS
styling, layout, painting, and user interaction—in a small, readable codebase.

The project is based on [Web Browser Engineering](https://browser.engineering)
by Pavel Panchekha and Chris Harrelson, with the implementation adapted and
extended as a hands-on systems programming project.

## Current capabilities

- Fetches HTTP and HTTPS pages over raw sockets
- Handles HTTP/1.0 responses, redirects, persistent connections, custom ports,
  chunked transfer encoding, `gzip`, and `deflate`
- Supports `file://`, `data:`, and `view-source:` URLs
- Parses a subset of HTML and CSS, including inline and external stylesheets
- Lays out and renders styled text in a Tkinter window
- Renders basic inline `<input>` fields and `<button>` controls, including
  input values and button labels
- Supports clickable links, back/forward navigation, scrolling, and window
  resizing
- Includes browser chrome with a tab strip, new-tab control, back and forward
  buttons, and current-page display
- Supports multiple tabs and switching between them
- Supports fragment links, including scrolling to matching `id` and `name`
  targets
- Reflows the document when the browser window is resized

## Roadmap

The completed work below covers the browser interface and navigation features
from Chapter 7 of the book. The remaining roadmap follows Chapters 8–16.

- [x] Implement hyperlinks and clickable `<a>` elements
- [x] Build browser chrome with tab and navigation controls
- [x] Add tabbed browsing and per-tab back/forward history
- [x] Chapter 8 — **Sending Information to Servers**: editable controls,
  form submission, HTTP `POST` requests, and web applications
- [ ] Chapter 9 — **Running Interactive Scripts**: JavaScript execution, DOM
  manipulation, event handling, and event defaults
- [ ] Chapter 10 — **Keeping Data Private**: cookies, same-origin policy,
  cross-site request forgery protection, SameSite cookies, XSS, and CSP
- [ ] Chapter 11 — **Adding Visual Effects**: Skia/SDL rendering, rasterization,
  compositing, transparency, blending, clipping, and masking
- [ ] Chapter 12 — **Scheduling Tasks and Threads**: task queues, timers,
  animation frames, profiling, multithreading, and threaded scrolling/layout
- [ ] Chapter 13 — **Animating and Compositing**: JavaScript and CSS animations,
  GPU acceleration, transitions, transforms, and composited layers
- [ ] Chapter 14 — **Making Content Accessible**: zoom, dark mode, keyboard
  navigation, focus indicators, accessibility trees, and screen readers
- [ ] Chapter 15 — **Supporting Embedded Content**: images, interactive
  widgets, iframes, frame scripts, cross-frame messaging, and isolation
- [ ] Chapter 16 — **Reusing Previous Computations**: incremental DOM, style,
  and layout updates through invalidation and dependency tracking

## Requirements

- Python 3.12 or newer
- Tkinter, included with most Python installations

The browser uses only Python’s standard library; no third-party packages are
required.

## Run

From the project directory, pass a URL to `main.py`:

```bash
python main.py https://example.com
```

Other supported URL forms include:

```bash
# Open a local HTML file
python main.py file:///absolute/path/to/page.html

# Render inline HTML
python main.py 'data:text/html,<h1>Hello</h1><p>Welcome!</p>'

# Display a page’s raw response body
python main.py view-source:https://example.com
```

The command-line entry point expects exactly one URL:

```text
Usage: python main.py URL
```

## Controls

- Click `+` to open a new tab.
- Click `<` to go back in the active tab.
- Click `>` to go forward after going back in the active tab.
- Click a tab to make it active.
- Click links in a page to navigate.
- Click the address bar to enter a URL. Hosts ending in `.com`, `.org`, or
  `.engineering` are opened over HTTPS; other text is searched with Google.
- Press `Enter` to submit the address bar, or `BackSpace` to edit it.
- Use the mouse wheel, `Up`/`Down` keys, or the scrollbar to scroll.

## Project structure

- `main.py` — command-line entry point
- `browser/networking/` — URL parsing, socket connections, TLS, and response decoding
- `browser/html/` — HTML parsing and document tree types
- `browser/css/` — CSS parsing, selectors, and styling
- `browser/layout/` — document, block, line, text, and form-control layout
- `browser/rendering/` — drawing commands and font helpers
- `browser/ui/` — Tkinter UI, tabs, and navigation

## Status

This is an active work-in-progress. The browser intentionally supports only a
subset of modern web standards, so many real-world pages will render
incompletely. The roadmap above documents the next major implementation steps.

## Acknowledgments

This project follows the structure and approach of the excellent free book
[Web Browser Engineering](https://browser.engineering) by Pavel Panchekha and
Chris Harrelson.
