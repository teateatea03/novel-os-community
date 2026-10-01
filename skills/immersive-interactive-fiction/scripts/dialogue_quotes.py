"""Scan complete Chinese dialogue quotes without silently dropping long text."""
from __future__ import annotations


def parse_dialogue_quotes(text: str) -> tuple[list[tuple[int, str]], list[str]]:
    """Return (opening offset, full quote) pairs and structural parse errors.

    Narration without quote delimiters is valid and returns two empty lists.
    Nested same-style, empty, or unmatched delimiters require correction; they
    must never be treated as a scene that simply contains no dialogue.
    """
    quotes = []
    errors = []
    opening = None
    for index, char in enumerate(text):
        if char == '「':
            if opening is not None:
                errors.append('nested dialogue quotation is unsupported')
            else:
                opening = index
        elif char == '」':
            if opening is None:
                errors.append('dialogue closing quotation has no opening delimiter')
            else:
                quote = text[opening + 1:index]
                quotes.append((opening, quote))
                if not quote.strip():
                    errors.append('empty dialogue quotation is unsupported')
                opening = None
    if opening is not None:
        errors.append('dialogue opening quotation has no closing delimiter')
    return quotes, errors
