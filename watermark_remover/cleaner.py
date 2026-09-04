"""Dispatch cleaning to the right per-format cleaner, then verify the result."""

from __future__ import annotations

from . import detector, formats, image_layer, office_layer, pdf_layer, text_layer

# Formats where a zero indicator_count after cleaning is an honest, verifiable
# guarantee (deterministic strip: the carrier bytes are simply not written back).
_VERIFIABLE_KINDS = {"text", "image", "pdf", "office"}


class UnsupportedFormatError(Exception):
    pass


def clean(name: str, data: bytes, normalize_spaces: bool = True, force_text: bool = False) -> dict:
    """Clean `data` and return a report with before/after scans and a
    `verified_clean` flag. Never claims certainty for formats/watermark
    classes this tool cannot deterministically strip and re-check.
    """
    kind = "text" if force_text else formats.classify(name, data)
    before = detector.inspect(name, data, force_text=force_text)

    if kind == "text":
        text = data.decode("utf-8", errors="replace")
        cleaned = text_layer.clean_text(text, normalize_spaces=normalize_spaces).encode("utf-8")
    elif kind == "image":
        cleaned = image_layer.clean_image(data)
    elif kind == "pdf":
        cleaned = pdf_layer.clean_pdf(data)
    elif kind == "office":
        cleaned = office_layer.clean_office(data)
    else:
        raise UnsupportedFormatError(
            f"'{name}' was classified as '{kind}': no deterministic cleaner for this "
            "format. Use --force-text to scan/clean it as plain text, or add a cleaner."
        )

    after = detector.inspect(name, cleaned, force_text=force_text)

    verified_clean = kind in _VERIFIABLE_KINDS and after["indicator_count"] == 0
    note = None
    if kind == "text" and verified_clean:
        note = (
            "Layer A (invisible-character) watermarks verifiably removed. "
            "This does NOT cover statistical/token-sampling watermarks "
            "(e.g. SynthID-text, Kirchenbauer green-list) — those require "
            "paraphrasing and cannot be certified without a vendor detector."
        )
    elif kind == "image" and verified_clean:
        note = (
            "EXIF/XMP/ICC/C2PA metadata verifiably removed by full re-encode. "
            "This does NOT cover pixel-domain watermarks (e.g. SynthID image) "
            "embedded in the image content itself."
        )

    return {
        "kind": kind,
        "before": before,
        "after": after,
        "verified_clean": verified_clean,
        "note": note,
        "cleaned_bytes": cleaned,
    }
