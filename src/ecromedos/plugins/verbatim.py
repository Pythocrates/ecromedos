# Desc:    This file is part of the ecromedos Document Preparation System
# Author:  Tobias Koch <tobias@tobijk.de>
# License: MIT
# URL:     http://www.ecromedos.net


def getInstance(config):
    """Returns a plugin instance."""
    return Plugin(config)


class Plugin:
    def __init__(self, config):
        pass

    def process(self, node, format):
        """Prepare @node for target @format."""

        tab_spaces = int(node.attrib.get("tabspaces", "4"))

        if format.endswith("latex"):
            self.verbatimString = self.LaTeX_verbatimString
        else:
            self.verbatimString = self.XHTML_verbatimString

        for child in node.iter():
            if child.text:
                child.text = self.verbatimString(child.text, tab_spaces)
            if child != node:
                if child.tail:
                    child.tail = self.verbatimString(child.tail, tab_spaces)

        return node

    def flush(self):
        pass

    def XHTML_verbatimString(self, string, tab_spaces):
        """Replaces tabs with spaces."""

        frame_start = 0
        frame_end = 0
        parts = []
        length = len(string)
        while frame_end < length:
            ch = string[frame_end]
            if ch == "\t":
                parts.append(string[frame_start:frame_end])
                parts.append(" " * tab_spaces)
                frame_end += 1
                frame_start = frame_end
            else:
                frame_end += 1

        if frame_end > frame_start:
            parts.append(string[frame_start:frame_end])

        return "".join(parts)

    def LaTeX_verbatimString(self, string, tab_spaces):
        """Replace any character that could have a special meaning in some
        context in LaTeX with a macro. But don't touch whitespace."""

        lookup_table = {
            "[": "{[}",
            "]": "{]}",
            "{": "\\{{}",
            "}": "\\}{}",
            "#": "\\#{}",
            "&": "\\&{}",
            "_": "\\_{}",
            "%": "\\%{}",
            "$": "\\${}",
            "^": "\\^{}",
            "\\": "\\textbackslash{}",
            "~": "\\textasciitilde{}",
            "-": "{}{-}{}",
            ":": "{}{:}{}",
            ";": "{}{;}{}",
            "!": "{}{!}{}",
            "?": "{}{?}{}",
            '"': '{}{"}{}',
            "`": "{}{`}{}",
            "'": "{}{'}{}",
            "=": "{}{=}{}",
            "\t": "\t",
        }

        frame_start = 0
        frame_end = 0
        parts = []
        length = len(string)

        while frame_end < length:
            ch = string[frame_end]
            # look for translation
            try:
                escape_sequence = lookup_table[ch]
            except KeyError:
                escape_sequence = ""
            if escape_sequence:
                if frame_end > frame_start:
                    parts.append(string[frame_start:frame_end])
                if ch == "\t":
                    parts.append(" " * tab_spaces)
                else:
                    parts.append(escape_sequence)
                frame_end += 1
                frame_start = frame_end
            else:
                frame_end += 1

        if frame_end > frame_start:
            parts.append(string[frame_start:frame_end])

        return "".join(parts)
