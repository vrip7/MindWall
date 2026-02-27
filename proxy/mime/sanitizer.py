"""
MindWall — HTML Sanitizer
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Strips HTML tags and normalizes whitespace to produce clean plain text
for LLM analysis.
"""

import re
from html import unescape

import structlog

logger = structlog.get_logger(__name__)


class HTMLSanitizer:
    """
    Converts HTML content to clean plain text suitable for LLM analysis.
    Strips all tags, decodes entities, and normalizes whitespace.
    """

    # Patterns for HTML removal
    SCRIPT_STYLE_PATTERN = re.compile(
        r'<(script|style)[^>]*>.*?</(script|style)>',
        re.IGNORECASE | re.DOTALL,
    )
    TAG_PATTERN = re.compile(r'<[^>]+>')
    WHITESPACE_PATTERN = re.compile(r'\s+')
    NEWLINE_PATTERN = re.compile(r'\n{3,}')

    # Block-level elements that should produce line breaks
    BLOCK_ELEMENTS = re.compile(
        r'</?(?:div|p|br|h[1-6]|ul|ol|li|table|tr|td|th|blockquote|pre|hr|section|article|header|footer|nav)[^>]*>',
        re.IGNORECASE,
    )

    def sanitize(self, content: str) -> str:
        """
        Convert HTML or text content to clean plain text.

        Args:
            content: Raw HTML or text content.

        Returns:
            Clean plain-text string with normalized whitespace.
        """
        if not content:
            return ""

        text = content

        # Remove script and style blocks
        text = self.SCRIPT_STYLE_PATTERN.sub("", text)

        # Replace block elements with newlines
        text = self.BLOCK_ELEMENTS.sub("\n", text)

        # Replace <br> variants
        text = re.sub(r'<br\s*/?\s*>', '\n', text, flags=re.IGNORECASE)

        # Strip remaining HTML tags
        text = self.TAG_PATTERN.sub("", text)

        # Decode HTML entities
        text = unescape(text)

        # Normalize whitespace (but preserve intentional newlines)
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            cleaned = self.WHITESPACE_PATTERN.sub(" ", line).strip()
            if cleaned:
                cleaned_lines.append(cleaned)

        text = "\n".join(cleaned_lines)

        # Collapse excessive newlines
        text = self.NEWLINE_PATTERN.sub("\n\n", text)

        return text.strip()
