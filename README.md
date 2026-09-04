# watermarks_remover

Detect and strip AI-provenance / watermark data from files, then **verify** removal by re-scanning the cleaned output.

## Supported formats

| Format | What's stripped | Verification |
| --- | --- | --- |
| Text (`.txt`, `.md`, `.html`, `.json`, ...) | Invisible Unicode carriers: zero-width space/joiner, word joiner, BOM, soft hyphen, bidi controls, variation selectors, Unicode tag characters; unusual spaces normalized | Re-scan for the same codepoints — guaranteed 0 after clean |
| Images (PNG, JPEG, WebP, BMP, GIF, TIFF, ...) | EXIF, ICC profile, XMP, C2PA/JUMBF chunks | Full pixel re-encode with no metadata carried over — guaranteed 0 after clean |
| PDF | `/Info` dictionary, XMP metadata stream | Rebuild via `pypdf`, info dict cleared — guaranteed 0 after clean |
| Office (`.docx`, `.xlsx`, `.pptx`, `.odt`, ...) | `docProps/core.xml` fields (author, etc.), `docProps/custom.xml`, thumbnails | Re-scan zip parts — guaranteed 0 after clean |

**Honesty limit:** statistical/token-sampling text watermarks (SynthID-text, Kirchenbauer green-list) and pixel-domain image watermarks (SynthID image) are **not** removed by this tool — they require paraphrasing / regeneration and can't be certified without a vendor detector. The tool never reports `verified_clean: true` for a class of watermark it didn't actually check.

## Install

```bash
pip install -r requirements.txt
```

## CLI

```bash
python3 -m watermark_remover.cli inspect path/to/file
python3 -m watermark_remover.cli clean path/to/file -o path/to/file.cleaned.ext
```

`clean` prints a before/after report and exits non-zero if it can't verify the file is fully clean.

## Web app

```bash
python3 -m watermark_remover.webapp
# http://127.0.0.1:8765
```

Upload a file, get a before/after report and a download link for the cleaned file.

## Tests

```bash
pip install pytest
python3 -m pytest tests/ -v
```

## Credit

Approach and terminology (Layer A invisible-character stripping, C2PA/EXIF/XMP metadata stripping, detect-then-verify workflow) inspired by [guillaumemeyer/watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover). This is an independent, simplified stdlib+Pillow+pypdf+Flask implementation — it does not vendor that project's code, Docker images, or ML-backed statistical-watermark rewriting.
