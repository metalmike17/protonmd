"""Minimal parser for Valve's text KeyValues format (.vdf / .acf)."""
import re

_TOKEN = re.compile(r'"((?:[^"\\]|\\.)*)"|([{}])')


def _unescape(s):
    return s.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n").replace("\\t", "\t")


def loads(text):
    stack = [{}]
    key = None
    for m in _TOKEN.finditer(text):
        s, brace = m.groups()
        if brace == "{":
            new = {}
            stack[-1][key] = new
            stack.append(new)
            key = None
        elif brace == "}":
            if len(stack) > 1:
                stack.pop()
            key = None
        elif key is None:
            key = _unescape(s)
        else:
            stack[-1][key] = _unescape(s)
            key = None
    return stack[0]


def load(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return loads(f.read())


def get(d, *path, default=None):
    """Case-insensitive nested lookup (Steam is inconsistent about key case)."""
    for p in path:
        if not isinstance(d, dict):
            return default
        found = next((v for k, v in d.items() if k.lower() == p.lower()), None)
        if found is None:
            return default
        d = found
    return d
