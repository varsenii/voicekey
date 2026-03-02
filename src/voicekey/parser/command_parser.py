class CommandParser:

    NAMED = {
        "enter": b"\n",
        "return": b"\n",
        "tab": b"\t",
        "space": b" ",
        "backspace": b"\x7f",
        "escape": b"\x1b",
        "esc": b"\x1b",
    }

    ARROWS = {
        "up arrow": b"\x1b[A",
        "down arrow": b"\x1b[B",
        "right arrow": b"\x1b[C",
        "left arrow": b"\x1b[D",
    }

    def parse(self, text: str):
        text = text.lower().strip()

        if text.startswith("press "):
            return self._parse_press(text[6:].strip())

        if text.startswith("type "):
            return text[5:].encode()

        return None

    def _parse_press(self, content: str):
        if content in self.NAMED:
            return self.NAMED[content]

        if content in self.ARROWS:
            return self.ARROWS[content]

        if content.startswith(("control ", "ctrl ")):
            parts = content.split()
            key = parts[-1]
            if len(key) == 1:
                return bytes([ord(key) & 0x1F])

        if len(content) == 1:
            return content.encode()

        return content.encode()