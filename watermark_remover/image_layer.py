"""Detect and strip EXIF/XMP/ICC/C2PA provenance data from images."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

_PROVENANCE_MARKERS = (b"c2pa", b"C2PA", b"jumb", b"JUMB", b"xmp", b"XMP", b"http://ns.adobe.com/xap")

# Pillow's `Image.info` mixes structural, format-inherent fields (present on
# every file of that format, not carriers of provenance data) with actual
# metadata/text chunks. Only the latter should count as a watermark signal.
_STRUCTURAL_INFO_KEYS = {
    "jfif", "jfif_version", "jfif_unit", "jfif_density", "dpi", "adobe",
    "adobe_transform", "progressive", "progression", "interlace",
    "transparency", "gamma", "aspect", "loop", "duration", "background",
    "extension", "version", "mode",
}


def scan_image(data: bytes) -> dict:
    """Report EXIF/XMP/ICC/C2PA-ish signals found in raw image bytes."""
    report: dict = {"categories": {}, "sample_positions": []}
    marker_hits = 0
    for marker in _PROVENANCE_MARKERS:
        count = data.count(marker)
        if count:
            marker_hits += count
            report["categories"][f"raw byte marker: {marker.decode('ascii', 'replace')}"] = count

    exif_tags = 0
    icc_present = False
    text_chunks = 0
    try:
        with Image.open(BytesIO(data)) as im:
            exif = im.getexif()
            exif_tags = len(exif) if exif else 0
            icc_present = "icc_profile" in im.info and bool(im.info["icc_profile"])
            text_chunks = sum(
                1 for k in im.info if k not in ("icc_profile", "exif") and k not in _STRUCTURAL_INFO_KEYS
            )
    except Exception:
        pass

    if exif_tags:
        report["categories"]["EXIF tags"] = exif_tags
    if icc_present:
        report["categories"]["ICC profile"] = 1
    if text_chunks:
        report["categories"]["ancillary text/metadata chunks"] = text_chunks

    report["indicator_count"] = marker_hits + exif_tags + (1 if icc_present else 0) + text_chunks
    return report


def clean_image(data: bytes) -> bytes:
    """Decode pixels and re-encode fresh, dropping all metadata/ancillary chunks."""
    with Image.open(BytesIO(data)) as im:
        fmt = im.format or "PNG"
        im.load()
        out = BytesIO()
        save_kwargs = {}
        if fmt.upper() in ("JPEG", "JPG"):
            save_kwargs["quality"] = 95
        # Deliberately do not pass exif=/icc_profile=/pnginfo=: Pillow only
        # writes those chunks when given explicit data, so omitting them is
        # what strips EXIF/XMP/ICC/C2PA on re-save.
        im.save(out, format=fmt, **save_kwargs)
        return out.getvalue()
