import sys

from browser.browser import Browser


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py URL")
        sys.exit(1)

    browser = Browser()
    browser.load(sys.argv[1])
    browser.window.mainloop()


if __name__ == "__main__":
    main()