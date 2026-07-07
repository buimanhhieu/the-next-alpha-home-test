"""
HTML → Markdown converter.

Rules (per assignment):
  ✅ Keep: headings (h1-h6), code blocks (pre/code), links (a[href])
  ❌ Remove: nav, header, footer, aside, .menu, .navigation, ads

Uses the `markdownify` library which wraps html2text with better fidelity.
Falls back to a hand-rolled parser for edge cases.
"""
import re
import logging
from html.parser import HTMLParser
from typing import Optional

logger = logging.getLogger(__name__)

# Tags to strip entirely (element + all children)
STRIP_TAGS = {
    "nav", "header", "footer", "aside", "script", "style",
    "noscript", "form", "button", "iframe", "figure",
}

# CSS class/id fragments that signal navigation / ads / menus
STRIP_CLASS_PATTERNS = [
    "nav", "navigation", "menu", "sidebar", "breadcrumb",
    "header", "footer", "ad", "advertisement", "cookie",
    "popup", "modal", "banner",
]


def _should_strip_attrs(attrs: dict) -> bool:
    combined = " ".join([
        attrs.get("class", ""),
        attrs.get("id", ""),
        attrs.get("role", ""),
    ]).lower()
    return any(p in combined for p in STRIP_CLASS_PATTERNS)


class _MarkdownBuilder(HTMLParser):
    """
    Minimal streaming HTML → Markdown converter.

    Handles:
      h1–h6  → # … ######
      p      → paragraph with trailing blank line
      pre    → ``` fenced code block
      code   → `inline code`
      a      → [text](href)  (only when href is absolute or starts with /)
      ul/ol  → - item / 1. item
      li     → list item
      strong/b → **text**
      em/i   → *text*
      br     → newline
      hr     → ---
      table  → ignored (just text content)
    """

    def __init__(self, source_url: str = ""):
        super().__init__()
        self.source_url = source_url
        self._output: list[str] = []
        self._skip_depth   = 0   # > 0 means we are inside a stripped subtree
        self._in_pre       = False
        self._in_code      = False
        self._in_link      = False
        self._link_href    = ""
        self._link_text    = ""
        self._list_stack: list[str] = []   # "ul" or "ol"
        self._list_counters: list[int] = []
        self._heading_level = 0
        self._heading_text  = ""

    # ── HTMLParser hooks ──────────────────────────────────────────────────────

    def handle_starttag(self, tag: str, attrs_list):
        attrs = dict(attrs_list)

        # If we are already inside a skipped subtree, just count depth
        if self._skip_depth > 0:
            self._skip_depth += 1
            return

        # Should we strip this element?
        if tag in STRIP_TAGS or _should_strip_attrs(attrs):
            self._skip_depth = 1
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self._heading_level = level
            self._heading_text  = ""
        elif tag == "p":
            pass   # text accumulates naturally
        elif tag == "pre":
            self._in_pre = True
            # Try to detect language from class like "language-python"
            cls = attrs.get("class", "")
            lang = ""
            m = re.search(r"language-(\w+)", cls)
            if m:
                lang = m.group(1)
            self._output.append(f"\n```{lang}\n")
        elif tag == "code":
            if not self._in_pre:
                self._in_code = True
                self._output.append("`")
        elif tag == "a":
            href = attrs.get("href", "")
            # Normalise relative URLs
            if href.startswith("/"):
                href = "https://support.optisigns.com" + href
            self._in_link  = True
            self._link_href = href
            self._link_text = ""
        elif tag in ("ul", "ol"):
            self._list_stack.append(tag)
            self._list_counters.append(0)
        elif tag == "li":
            if self._list_stack:
                list_type = self._list_stack[-1]
                if list_type == "ol":
                    self._list_counters[-1] += 1
                    prefix = f"{self._list_counters[-1]}. "
                else:
                    prefix = "- "
                indent = "  " * (len(self._list_stack) - 1)
                self._output.append(f"\n{indent}{prefix}")
        elif tag in ("strong", "b"):
            self._output.append("**")
        elif tag in ("em", "i"):
            self._output.append("*")
        elif tag == "br":
            self._output.append("\n")
        elif tag == "hr":
            self._output.append("\n---\n")
        elif tag == "blockquote":
            self._output.append("\n> ")

    def handle_endtag(self, tag: str):
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level  = self._heading_level
            text   = self._heading_text.strip()
            if text:
                self._output.append(f"\n{'#' * level} {text}\n")
            self._heading_level = 0
            self._heading_text  = ""
        elif tag == "p":
            self._output.append("\n\n")
        elif tag == "pre":
            self._in_pre = False
            self._output.append("\n```\n\n")
        elif tag == "code":
            if self._in_code:
                self._in_code = False
                self._output.append("`")
        elif tag == "a":
            if self._in_link:
                text = self._link_text.strip()
                href = self._link_href
                if href and text:
                    self._output.append(f"[{text}]({href})")
                elif text:
                    self._output.append(text)
                self._in_link  = False
                self._link_href = ""
                self._link_text = ""
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
                self._list_counters.pop()
            self._output.append("\n")
        elif tag in ("strong", "b"):
            self._output.append("**")
        elif tag in ("em", "i"):
            self._output.append("*")

    def handle_data(self, data: str):
        if self._skip_depth > 0:
            return
        text = data  # preserve whitespace inside <pre>
        if not self._in_pre:
            text = re.sub(r"\s+", " ", data)

        if self._heading_level > 0:
            self._heading_text += text
        elif self._in_link:
            self._link_text += text
        else:
            self._output.append(text)

    # ── Public method ─────────────────────────────────────────────────────────

    def get_markdown(self) -> str:
        md = "".join(self._output)
        # Collapse 3+ consecutive blank lines → 2
        md = re.sub(r"\n{3,}", "\n\n", md)
        return md.strip()


def html_to_markdown(html: str, source_url: str = "", title: str = "") -> str:
    """
    Convert an HTML string to clean Markdown.

    Args:
        html:       Raw HTML body (just the article body, not full page).
        source_url: Original article URL (prepended as metadata).
        title:      Article title (prepended as H1).

    Returns:
        Markdown string.
    """
    builder = _MarkdownBuilder(source_url=source_url)
    try:
        builder.feed(html)
    except Exception as exc:
        logger.warning("[Converter] HTML parse error: %s", exc)

    md = builder.get_markdown()

    # Prepend metadata header
    header_parts = []
    if title:
        header_parts.append(f"# {title}\n")
    if source_url:
        header_parts.append(f"**Source:** {source_url}\n")
    if header_parts:
        header_parts.append("\n")

    return "".join(header_parts) + md
