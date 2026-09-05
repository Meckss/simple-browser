# Simple Browser

A minimal web browser built from scratch in Python.

This project is an educational implementation of a basic browser that
fetches and displays web pages. It currently supports HTTP, HTTPS, and
local files.

## Features

- HTTP and HTTPS support
- `file://` scheme for opening local files
- `data:` scheme for inline HTML and text
- `view-source` scheme for viewing raw HTML
- HTTP/1.0 requests
- Basic HTML tag stripping for text-only rendering
- Custom `User-Agent` header
- Custom ports in URLs

## Requirements

- Python 3.12.3

## How to Run

Open a website:

```bash
python browser.py https://example.com
``` 

## How to Run

```bash
# Open a website
python browser.py https://example.com

# Open a local file
python browser.py file:///path/to/your/file.html
```

## Acknowledgments

This project is based on the excellent free book  
[Web Browser Engineering](https://browser.engineering)  
by Pavel Panchekha and Chris Harrelson.

The structure and approach follow the book closely as a learning exercise.

## Status

Work in progress. More features (better HTML parsing, layout, etc.) will be added over time.