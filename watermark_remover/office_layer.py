"""Detect and strip provenance/author metadata from OOXML/ODF containers
(.docx, .xlsx, .pptx, .odt, .ods, .odp — all zip archives of XML parts)."""

from __future__ import annotations

import re
import zipfile
from io import BytesIO

_METADATA_PARTS = {"docProps/core.xml", "docProps/app.xml", "meta.xml"}
_DROP_PARTS = {"docProps/custom.xml", "docProps/thumbnail.jpeg", "docProps/thumbnail.png"}

# Fields inside core.xml / meta.xml worth blanking (author, timestamps, app id).
_SCRUB_TAGS = (
    "dc:creator",
    "cp:lastModifiedBy",
    "dc:description",
    "dc:subject",
    "cp:keywords",
    "cp:category",
    "meta:initial-creator",
    "meta:generator",
)


def _scrub_xml_text(xml_bytes: bytes) -> bytes:
    text = xml_bytes.decode("utf-8", errors="replace")
    for tag in _SCRUB_TAGS:
        text = re.sub(rf"(<{tag}[^>]*>)(.*?)(</{tag}>)", r"\1\3", text, flags=re.DOTALL)
    return text.encode("utf-8")


def scan_office(data: bytes) -> dict:
    report: dict = {"categories": {}, "sample_positions": []}
    count = 0
    try:
        with zipfile.ZipFile(BytesIO(data)) as zf:
            names = zf.namelist()
            for part in _DROP_PARTS:
                if part in names:
                    report["categories"][f"metadata part: {part}"] = 1
                    count += 1
            for part in _METADATA_PARTS:
                if part in names:
                    xml = zf.read(part).decode("utf-8", errors="replace")
                    for tag in _SCRUB_TAGS:
                        m = re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", xml, flags=re.DOTALL)
                        non_empty = [v for v in m if v.strip()]
                        if non_empty:
                            report["categories"][f"{part}:{tag}"] = len(non_empty)
                            count += len(non_empty)
            for name in names:
                if name.lower() == "docprops/custom.xml":
                    continue
                lower_name = name.lower()
                if lower_name.endswith(".xml"):
                    blob = zf.read(name)
                    for marker in (b"c2pa", b"C2PA", b"jumb", b"JUMB"):
                        n = blob.count(marker)
                        if n:
                            report["categories"][f"raw marker {marker.decode()} in {name}"] = n
                            count += n
    except zipfile.BadZipFile:
        pass

    report["indicator_count"] = count
    return report


def clean_office(data: bytes) -> bytes:
    out = BytesIO()
    with zipfile.ZipFile(BytesIO(data)) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename in _DROP_PARTS:
                continue
            payload = zin.read(item.filename)
            if item.filename in _METADATA_PARTS:
                payload = _scrub_xml_text(payload)
            zout.writestr(item, payload)
    return out.getvalue()
