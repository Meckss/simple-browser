"""Local and inline resource loading."""

import base64
import binascii
import urllib.parse


def load_local(page):
    if page.scheme == "data":
        try:
            metadata, data = page.data.split(",", 1)
        except ValueError as error:
            raise ValueError("Invalid data URL: missing comma") from error
        if metadata.endswith(";base64"):
            try:
                content = base64.b64decode(data)
            except (ValueError, binascii.Error) as error:
                raise ValueError("Invalid base64 data URL") from error
        else:
            content = urllib.parse.unquote_to_bytes(data)
        return content.decode("utf-8", errors="replace")
    try:
        with open(page.path, "r", encoding="utf8") as file:
            return file.read()
    except FileNotFoundError as error:
        raise FileNotFoundError(f"File not found: {page.path}") from error
    except PermissionError as error:
        raise PermissionError(f"Permission denied: {page.path}") from error
