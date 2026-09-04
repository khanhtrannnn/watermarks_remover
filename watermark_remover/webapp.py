"""Minimal web app: upload a file, clean it, download the result, see the
before/after verification report."""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from . import cleaner

MAX_UPLOAD_MB = int(os.environ.get("WM_MAX_UPLOAD_MB", "25"))
STORE_DIR = Path(os.environ.get("WM_STORE_DIR", "/tmp/watermark-remover-store"))
STORE_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


@app.get("/")
def index():
    return render_template("index.html", result=None)


@app.post("/clean")
def clean_upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return render_template("index.html", result=None, error="Choose a file first."), 400

    data = file.read()
    try:
        result = cleaner.clean(file.filename, data, normalize_spaces="normalize_spaces" in request.form)
    except cleaner.UnsupportedFormatError as exc:
        return render_template("index.html", result=None, error=str(exc)), 400

    token = uuid.uuid4().hex
    out_name = secure_filename(f"cleaned_{Path(file.filename).name}") or "cleaned_file"
    (STORE_DIR / f"{token}_{out_name}").write_bytes(result["cleaned_bytes"])

    return render_template(
        "index.html",
        result={
            "filename": file.filename,
            "kind": result["kind"],
            "before": result["before"],
            "after": result["after"],
            "verified_clean": result["verified_clean"],
            "note": result["note"],
            "download_url": url_for("download", token=token, name=out_name),
        },
        error=None,
    )


_TOKEN_RE = re.compile(r"^[0-9a-f]{32}$")


@app.get("/download/<token>/<name>")
def download(token: str, name: str):
    name = secure_filename(name)
    if not _TOKEN_RE.match(token) or not name:
        return redirect(url_for("index"))
    path = (STORE_DIR / f"{token}_{name}").resolve()
    if path.parent != STORE_DIR.resolve() or not path.exists():
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name=name)


def main():
    app.run(host=os.environ.get("WM_HOST", "127.0.0.1"), port=int(os.environ.get("WM_PORT", "8765")))


if __name__ == "__main__":
    main()
