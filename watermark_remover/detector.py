"""Dispatch inspection to the right per-format detector."""

from __future__ import annotations

from . import formats, image_layer, office_layer, pdf_layer, text_layer


def inspect(name: str, data: bytes, force_text: bool = False) -> dict:
    kind = "text" if force_text else formats.classify(name, data)

    if kind == "text":
        text = data.decode("utf-8", errors="replace")
        report = text_layer.scan_text(text)
    elif kind == "image":
        report = image_layer.scan_image(data)
    elif kind == "pdf":
        report = pdf_layer.scan_pdf(data)
    elif kind == "office":
        report = office_layer.scan_office(data)
    else:
        report = {"categories": {}, "sample_positions": [], "indicator_count": 0, "unsupported": True}

    report["kind"] = kind
    report["suspicious"] = report.get("indicator_count", 0) > 0
    return report
