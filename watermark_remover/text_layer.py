"""Detect and strip invisible-Unicode watermark carriers from text."""

from __future__ import annotations

import unicodedata

# Characters that are never legitimate in normal prose and are the usual
# carriers for zero-width / steganographic watermarking. Keyed by codepoint
# (not literal chars) so the source stays free of invisible bytes.
_ALWAYS_STRIP = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE / BOM",
    0x00AD: "SOFT HYPHEN",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0x2061: "FUNCTION APPLICATION",
    0x2062: "INVISIBLE TIMES",
    0x2063: "INVISIBLE SEPARATOR",
    0x2064: "INVISIBLE PLUS",
}

_BIDI_CONTROLS = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
_VARIATION_SELECTORS = set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0))
_TAG_CHARS = set(range(0xE0000, 0xE0080))

# Unusual spaces sometimes used to encode watermark bits via alternation.
_UNUSUAL_SPACES = {
    0x00A0: "NO-BREAK SPACE",
    0x2000: "EN QUAD",
    0x2001: "EM QUAD",
    0x2002: "EN SPACE",
    0x2003: "EM SPACE",
    0x2004: "THREE-PER-EM SPACE",
    0x2005: "FOUR-PER-EM SPACE",
    0x2006: "SIX-PER-EM SPACE",
    0x2007: "FIGURE SPACE",
    0x2008: "PUNCTUATION SPACE",
    0x2009: "THIN SPACE",
    0x200A: "HAIR SPACE",
    0x202F: "NARROW NO-BREAK SPACE",
    0x205F: "MEDIUM MATHEMATICAL SPACE",
    0x3000: "IDEOGRAPHIC SPACE",
}


def _classify_char(cp: int) -> str | None:
    if cp in _ALWAYS_STRIP:
        return _ALWAYS_STRIP[cp]
    if cp in _BIDI_CONTROLS:
        return "BIDI CONTROL"
    if cp in _VARIATION_SELECTORS:
        return "VARIATION SELECTOR"
    if cp in _TAG_CHARS:
        return "UNICODE TAG CHARACTER"
    if cp in _UNUSUAL_SPACES:
        return f"UNUSUAL SPACE ({_UNUSUAL_SPACES[cp]})"
    return None


def scan_text(text: str) -> dict:
    """Return a report of invisible/watermark-carrier characters found."""
    findings: dict[str, int] = {}
    positions: list[int] = []
    for i, ch in enumerate(text):
        label = _classify_char(ord(ch))
        if label:
            findings[label] = findings.get(label, 0) + 1
            positions.append(i)
    return {
        "indicator_count": sum(findings.values()),
        "categories": findings,
        "sample_positions": positions[:20],
    }


def clean_text(text: str, normalize_spaces: bool = True) -> str:
    """Strip invisible watermark carriers; optionally fold unusual spaces to U+0020."""
    out = []
    for ch in text:
        cp = ord(ch)
        if cp in _ALWAYS_STRIP or cp in _BIDI_CONTROLS or cp in _VARIATION_SELECTORS or cp in _TAG_CHARS:
            continue
        if normalize_spaces and cp in _UNUSUAL_SPACES:
            out.append(" ")
            continue
        out.append(ch)
    cleaned = "".join(out)
    return unicodedata.normalize("NFC", cleaned)
