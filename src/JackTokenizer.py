import re
import os
from typing import List, Tuple

KEYWORDS = {
    "class", "constructor", "function", "method", "field", "static",
    "var", "int", "char", "boolean", "void", "true", "false", "null",
    "this", "let", "do", "if", "else", "while", "return",
}

SYMBOLS = set("{}()[].,;+-*/&|<>=~")

XML_ESCAPE = {
    "<":  "&lt;",
    ">":  "&gt;",
    "&":  "&amp;",
    '"':  "&quot;",
}

class JackTokenizer:
    def __init__(self, source_path: str):
        self._source_path = source_path
        self._tokens: List[Tuple[str, str]] = []

    def tokenize(self) -> List[Tuple[str, str]]:
        with open(self._source_path, "r") as f:
            raw = f.read()

        clean = self._strip_comments(raw)
        self._tokens = self._scan(clean)
        self._write_xml()
        return self._tokens

    def _strip_comments(self, src: str) -> str:
        result = []
        i = 0
        n = len(src)
        in_block   = False
        in_line    = False
        in_string  = False

        while i < n:
            c = src[i]
            if in_string:
                result.append(c)
                if c == '"':
                    in_string = False
                i += 1
            elif in_line:
                if c == "\n":
                    result.append("\n")
                    in_line = False
                i += 1
            elif in_block:
                if c == "*" and i + 1 < n and src[i + 1] == "/":
                    in_block = False
                    i += 2
                else:
                    if c == "\n":
                        result.append("\n")
                    i += 1
            else:
                if c == '"':
                    in_string = True
                    result.append(c)
                    i += 1
                elif c == "/" and i + 1 < n and src[i + 1] == "/":
                    in_line = True
                    i += 2
                elif c == "/" and i + 1 < n and src[i + 1] == "*":
                    in_block = True
                    i += 2
                else:
                    result.append(c)
                    i += 1
        return "".join(result)

    def _scan(self, src: str) -> List[Tuple[str, str]]:
        tokens = []
        i = 0
        n = len(src)
        
        while i < n:
            c = src[i]
            if c in " \t\r\n":
                i += 1
                continue
            if c == '"':
                j = src.index('"', i + 1)
                tokens.append(("stringConstant", src[i + 1:j]))
                i = j + 1
                continue
            if c in SYMBOLS:
                tokens.append(("symbol", c))
                i += 1
                continue
            if c.isdigit():
                j = i
                while j < n and src[j].isdigit():
                    j += 1
                val = int(src[i:j])
                if val > 32767:
                    raise ValueError(f"Integer constant {val} out of range [0,32767]")
                tokens.append(("integerConstant", str(val)))
                i = j
                continue
            if c.isalpha() or c == "_":
                j = i
                while j < n and (src[j].isalnum() or src[j] == "_"):
                    j += 1
                word = src[i:j]
                if word in KEYWORDS:
                    tokens.append(("keyword", word))
                else:
                    tokens.append(("identifier", word))
                i = j
                continue
            i += 1
            
        return tokens

    def _write_xml(self):
        base = os.path.splitext(self._source_path)[0]
        out_path = base + "T.xml"
        with open(out_path, "w") as f:
            f.write("<tokens>\n")
            for ttype, tval in self._tokens:
                escaped = self._escape(tval)
                f.write(f"<{ttype}> {escaped} </{ttype}>\n")
            f.write("</tokens>\n")
        self._xml_path = out_path

    @staticmethod
    def _escape(val: str) -> str:
        for ch, esc in XML_ESCAPE.items():
            val = val.replace(ch, esc)
        return val