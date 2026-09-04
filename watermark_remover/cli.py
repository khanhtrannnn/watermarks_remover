"""Command-line interface: inspect / clean files, with post-clean verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import cleaner, detector


def _fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def _read_input(path: Path) -> bytes:
    if not path.exists():
        _fail(
            f"error: file not found: {path}\n"
            "(replace the path with a real file on your machine, e.g. C:\\Users\\you\\Documents\\notes.txt "
            "or ./notes.txt — 'path/to/file' in the README is a placeholder, not a literal path)"
        )
    if path.is_dir():
        _fail(f"error: '{path}' is a directory, not a file")
    try:
        return path.read_bytes()
    except PermissionError:
        _fail(f"error: permission denied reading '{path}'")


def _cmd_inspect(args: argparse.Namespace) -> int:
    in_path = Path(args.file)
    data = _read_input(in_path)
    report = detector.inspect(in_path.name, data, force_text=args.force_text)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["suspicious"] else 0


def _cmd_clean(args: argparse.Namespace) -> int:
    in_path = Path(args.file)
    data = _read_input(in_path)
    try:
        result = cleaner.clean(
            in_path.name, data, normalize_spaces=not args.no_normalize_spaces, force_text=args.force_text
        )
    except cleaner.UnsupportedFormatError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = Path(args.output) if args.output else in_path.with_name(in_path.stem + ".cleaned" + in_path.suffix)
    out_path.write_bytes(result["cleaned_bytes"])

    summary = {
        "kind": result["kind"],
        "input": str(in_path),
        "output": str(out_path),
        "indicators_before": result["before"]["indicator_count"],
        "indicators_after": result["after"]["indicator_count"],
        "verified_clean": result["verified_clean"],
        "note": result["note"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if not result["verified_clean"]:
        print(
            "\nWARNING: could not verify the file is fully clean "
            f"(indicators remaining: {result['after']['indicator_count']}, "
            f"details: {result['after']['categories']}).",
            file=sys.stderr,
        )
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="watermark-remover")
    sub = parser.add_subparsers(dest="command", required=True)

    p_inspect = sub.add_parser("inspect", help="scan a file for watermark/provenance indicators")
    p_inspect.add_argument("file")
    p_inspect.add_argument("--force-text", action="store_true", help="scan raw bytes as text")
    p_inspect.set_defaults(func=_cmd_inspect)

    p_clean = sub.add_parser("clean", help="strip watermark/provenance data and verify removal")
    p_clean.add_argument("file")
    p_clean.add_argument("-o", "--output")
    p_clean.add_argument("--no-normalize-spaces", action="store_true")
    p_clean.add_argument("--force-text", action="store_true")
    p_clean.set_defaults(func=_cmd_clean)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
