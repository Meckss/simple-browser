"""Command-line entry point for the browser application."""

import sys

from browser.browser import Browser


def main():
    """Load the URL supplied on the command line and start the UI loop."""
    if len(sys.argv) != 2:
        print("Usage: python main.py URL")
        sys.exit(1)

    browser = Browser()
    browser.load(sys.argv[1])
    browser.window.mainloop()


if __name__ == "__main__":
    main()
