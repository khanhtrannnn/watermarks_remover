from io import BytesIO

from PIL import Image
from pypdf import PdfWriter

from watermark_remover import cleaner, detector, formats, text_layer


def test_classify_text():
    assert formats.classify("a.txt", b"hello world") == "text"


def test_text_watermark_detected_and_removed():
    watermarked = "Hello​World­! Space here."
    report = text_layer.scan_text(watermarked)
    assert report["indicator_count"] > 0

    cleaned = text_layer.clean_text(watermarked)
    report_after = text_layer.scan_text(cleaned)
    assert report_after["indicator_count"] == 0
    assert "​" not in cleaned
    assert "­" not in cleaned


def test_clean_pipeline_text_verified():
    data = "Zero​Width​Watermark".encode("utf-8")
    result = cleaner.clean("note.txt", data)
    assert result["kind"] == "text"
    assert result["verified_clean"] is True
    assert result["after"]["indicator_count"] == 0


def test_image_exif_stripped():
    im = Image.new("RGB", (4, 4), color="red")
    buf = BytesIO()
    exif = im.getexif()
    exif[0x0131] = "SneakyAITool"  # Software tag
    im.save(buf, format="JPEG", exif=exif)
    data = buf.getvalue()

    before = detector.inspect("photo.jpg", data)
    assert before["indicator_count"] > 0

    result = cleaner.clean("photo.jpg", data)
    assert result["kind"] == "image"
    assert result["verified_clean"] is True
    assert result["after"]["indicator_count"] == 0


def test_pdf_metadata_stripped():
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Author": "AI Generator", "/Producer": "SomeAITool"})
    buf = BytesIO()
    writer.write(buf)
    data = buf.getvalue()

    before = detector.inspect("doc.pdf", data)
    assert before["indicator_count"] > 0

    result = cleaner.clean("doc.pdf", data)
    assert result["verified_clean"] is True
    assert result["after"]["indicator_count"] == 0


def test_unknown_format_rejected():
    data = bytes(range(256)) * 4
    try:
        cleaner.clean("mystery.bin", data)
    except cleaner.UnsupportedFormatError:
        pass
    else:
        raise AssertionError("expected UnsupportedFormatError")
