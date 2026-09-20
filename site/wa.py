"""Convert WhatsApp's own text formatting to HTML.

Posts are written the way they are pasted into WhatsApp: *bold*,
_italic_, paragraphs separated by blank lines, a bare URL at the end.
This module turns exactly that, and nothing more, into HTML.
"""
import html
import re

BOLD = re.compile(r"\*(\S(?:[^*\n]*?\S)?)\*")
ITALIC = re.compile(r"_(\S(?:[^_\n]*?\S)?)_")
URL = re.compile(r"https?://[^\s<>\"]+")


def _format(segment: str) -> str:
    out = html.escape(segment, quote=True)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    return out


def inline(text: str) -> str:
    parts = []
    pos = 0
    for m in URL.finditer(text):
        parts.append(_format(text[pos:m.start()]))
        url = html.escape(m.group(0), quote=True)
        parts.append(f'<a href="{url}">{url}</a>')
        pos = m.end()
    parts.append(_format(text[pos:]))
    return "".join(parts)


def blocks(body: str) -> list[str]:
    return [b.strip() for b in re.split(r"\n\s*\n", body.strip()) if b.strip()]


def render_post(body: str) -> tuple[str, str]:
    bs = blocks(body)
    if not bs:
        return "", ""
    title = bs[0].strip().strip("*").strip()
    paragraphs = []
    for b in bs[1:]:
        cls = ' class="link"' if b.startswith("Read past updates:") else ""
        paragraphs.append(f"<p{cls}>{inline(b).replace(chr(10), '<br>' + chr(10))}</p>")
    return title, "\n".join(paragraphs)
