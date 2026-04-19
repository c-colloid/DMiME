#!/usr/bin/env python3
# DMiME - 医学医療用語変換辞書
# Copyright (C) 2016 Kmm, Project DMiME
# Licensed under GPL-2.0-or-later

"""Build Windows TSV and Mac plist dictionaries from the unified src/*.tsv.

This is the only tool that turns split sources into the shipped single-file
artifacts. It is used both locally (by contributors after editing src/) and
by CI (verify-split, sync-topfile, build-release workflows).

Usage:
    python3 scripts/build_release.py
    python3 scripts/build_release.py --dist=dist/

Without --dist the top-level shipped files are overwritten in-place:
    WindowsIME/DMiME-1.1.txt
    Mac/DMiME1.1 igakujisho for icloud.plist

With --dist the same files are also written to the given directory, suitable
for upload as GitHub Release assets.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _buckets import BUCKET_ORDER  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "src"
WIN_OUT = REPO / "WindowsIME" / "DMiME-1.1.txt"
MAC_OUT = REPO / "Mac" / "DMiME1.1 igakujisho for icloud.plist"

PLIST_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
    '<plist version="1.0">\n'
    '<array>\n'
)
PLIST_FOOTER = '</array>\n</plist>\n'


def load_entries() -> list[tuple[str, str, str, str]]:
    """Load rows in bucket order; each bucket sorted by (yomi, phrase)."""
    rows: list[tuple[str, str, str, str]] = []
    for name in BUCKET_ORDER:
        path = SRC_DIR / f"{name}.tsv"
        if not path.exists():
            continue
        bucket_rows: list[tuple[str, str, str, str]] = []
        with path.open(encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 4:
                    raise SystemExit(
                        f"{path}: expected 4 TSV columns, got {len(parts)}: {raw!r}"
                    )
                yomi, phrase, platform, pos = parts
                if platform not in ("win", "mac", "both"):
                    raise SystemExit(
                        f"{path}: unknown platform tag {platform!r} in {raw!r}"
                    )
                bucket_rows.append((yomi, phrase, platform, pos))
        bucket_rows.sort(key=lambda r: (r[0], r[1]))
        rows.extend(bucket_rows)
    return rows


def write_win(rows: list[tuple[str, str, str, str]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for yomi, phrase, platform, pos in rows:
            if platform in ("win", "both"):
                f.write(f"{yomi}\t{phrase}\t{pos}\t\n")
                written += 1
    return written


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def write_mac(rows: list[tuple[str, str, str, str]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(PLIST_HEADER)
        for yomi, phrase, platform, _pos in rows:
            if platform in ("mac", "both"):
                f.write(
                    f"<dict><key>shortcut</key><string>{_xml_escape(yomi)}</string>"
                    f"<key>phrase</key><string>{_xml_escape(phrase)}</string></dict>\n"
                )
                written += 1
        f.write(PLIST_FOOTER)
    return written


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", type=Path, default=None,
                    help="also copy outputs to this directory (for Release assets)")
    args = ap.parse_args()

    rows = load_entries()

    n_win = write_win(rows, WIN_OUT)
    n_mac = write_mac(rows, MAC_OUT)
    print(f"wrote {WIN_OUT.relative_to(REPO)}: {n_win} entries")
    print(f"wrote {MAC_OUT.relative_to(REPO)}: {n_mac} entries")

    if args.dist:
        args.dist.mkdir(parents=True, exist_ok=True)
        win_dist = args.dist / WIN_OUT.name
        mac_dist = args.dist / MAC_OUT.name
        win_dist.write_bytes(WIN_OUT.read_bytes())
        mac_dist.write_bytes(MAC_OUT.read_bytes())
        print(f"copied to {win_dist}")
        print(f"copied to {mac_dist}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
