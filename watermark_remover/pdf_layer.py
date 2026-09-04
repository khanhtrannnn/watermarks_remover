"""Detect and strip document-info metadata and XMP streams from PDFs."""

from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader, PdfWriter

_PROVENANCE_MARKERS = (b"c2pa", b"C2PA", b"jumb", b"JUMB", b"xmp", b"XMP", b"http://ns.adobe.com/xap")


def scan_pdf(data: bytes) -> dict:
    report: dict = {"categories": {}, "sample_positions": []}
    marker_hits = 0
    for marker in _PROVENANCE_MARKERS:
        count = data.count(marker)
        if count:
            marker_hits += count
            report["categories"][f"raw byte marker: {marker.decode('ascii', 'replace')}"] = count

    info_fields = 0
    xmp_present = False
    try:
        reader = PdfReader(BytesIO(data))
        if reader.metadata:
            info_fields = len(reader.metadata)
        xmp_present = reader.xmp_metadata is not None
    except Exception:
        pass

    if info_fields:
        report["categories"]["/Info dictionary fields"] = info_fields
    if xmp_present:
        report["categories"]["XMP metadata stream"] = 1

    report["indicator_count"] = marker_hits + info_fields + (1 if xmp_present else 0)
    return report


def clean_pdf(data: bytes) -> bytes:
    reader = PdfReader(BytesIO(data))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata({})
    # pypdf auto-populates /Producer on add_metadata/write; clear the info
    # dict outright so no library signature (or the source's own /Producer,
    # /Author, etc.) survives into the output.
    writer._info.get_object().clear()
    try:
        writer.xmp_metadata = None
    except Exception:
        pass
    root = writer._root_object
    if "/Metadata" in root:
        del root["/Metadata"]

    out = BytesIO()
    writer.write(out)
    return out.getvalue()
