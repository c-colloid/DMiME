#!/usr/bin/env python3
# DMiME - 医学医療用語変換辞書
# Copyright (C) 2016 Kmm, Project DMiME
# Licensed under GPL-2.0-or-later

"""Build Windows TSV and Mac plist dictionaries from the unified src/*.tsv.

This is the only tool that turns split sources into the shipped single-file
artifacts. It is used both locally (by contributors after editing src/) and
by CI (build-split and build-release workflows).

Usage:
    python3 scripts/build_release.py
    python3 scripts/build_release.py --dist=dist/ --version=1.2

Without --dist the version-less living files are (re)written in-place:
    WindowsIME/DMiME.txt
    Mac/DMiME igakujisho for icloud.plist

With --dist the release assets are written to the given directory. When
--version=X.Y is also given, artifact names carry that version:
    dist/DMiME-{version}.zip                           (Google 日本語入力用)
    dist/DMiME-{version}-msime.zip                     (Microsoft IME 用)
    dist/DMiME-{version} igakujisho for icloud.plist   (Mac ユーザ辞書用)

The MS IME file is UTF-16 LE with BOM + CRLF line endings and has
Google-specific POS tags ("サジェストのみ") stripped, since MS IME has
no equivalent concept.

When --version is omitted under --dist, the version-less names are used
(useful for manual testing).
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _buckets import BUCKET_ORDER, bucket_for  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "src"
SPECIAL_SRC = SRC_DIR / "_special.tsv"
WIN_OUT = REPO / "WindowsIME" / "DMiME.txt"
MAC_OUT = REPO / "Mac" / "DMiME igakujisho for icloud.plist"

PLIST_HEADER = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
    '<plist version="1.0">\n'
    '<array>\n'
)
PLIST_FOOTER = '</array>\n</plist>\n'


def _parse_row(path: Path, raw: str) -> tuple[str, str, str, str]:
    line = raw.rstrip("\n")
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
    return yomi, phrase, platform, pos


def load_entries() -> list[tuple[str, str, str, str]]:
    """Load rows in bucket order; each bucket sorted by (yomi, phrase).

    `_special.tsv` holds entries with non-conversion POS (短縮よみ / 抑制単語
    / サジェストのみ) so contributors can audit them in one place. Those rows
    are routed back to their natural 50音 bucket at build time, keeping the
    shipped artifact byte-identical with a layout where every entry was
    filed under its yomi's bucket.
    """
    buckets: dict[str, list[tuple[str, str, str, str]]] = {
        name: [] for name in BUCKET_ORDER
    }

    for name in BUCKET_ORDER:
        path = SRC_DIR / f"{name}.tsv"
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for raw in f:
                if not raw.strip() or raw.lstrip().startswith("#"):
                    continue
                buckets[name].append(_parse_row(path, raw))

    if SPECIAL_SRC.exists():
        with SPECIAL_SRC.open(encoding="utf-8") as f:
            for raw in f:
                if not raw.strip() or raw.lstrip().startswith("#"):
                    continue
                row = _parse_row(SPECIAL_SRC, raw)
                buckets[bucket_for(row[0])].append(row)

    rows: list[tuple[str, str, str, str]] = []
    for name in BUCKET_ORDER:
        buckets[name].sort(key=lambda r: (r[0], r[1]))
        rows.extend(buckets[name])
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


# Google 日本語入力 品詞 → Microsoft IME 品詞。
# None で落とすエントリ (MS IME に相当概念がないもの)。
MSIME_POS_MAP: dict[str, str | None] = {
    "名詞": "名詞",
    "固有名詞": "固有名詞",
    "短縮よみ": "短縮よみ",
    "名詞サ変": "サ変名詞",
    "抑制単語": "抑制単語",
    "サジェストのみ": None,
}


def write_msime(rows: list[tuple[str, str, str, str]], path: Path) -> int:
    """Write Microsoft IME-compatible user dictionary text.

    MS IME's text import requires UTF-16 LE with BOM and CRLF line
    endings, and accepts only its own POS vocabulary. POS tags that
    Google 日本語入力 ships but MS IME does not (e.g. "サジェストのみ")
    are dropped rather than forced into a non-equivalent category.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-16-le", newline="\r\n") as f:
        f.write("\ufeff")
        for yomi, phrase, platform, pos in rows:
            if platform not in ("win", "both"):
                continue
            mapped = MSIME_POS_MAP.get(pos)
            if mapped is None:
                continue
            f.write(f"{yomi}\t{phrase}\t{mapped}\n")
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


def build_release_assets(dist: Path, version: str | None,
                         rows: list[tuple[str, str, str, str]]) -> None:
    """Produce versioned Release assets.

    Three assets are produced per release:
      - DMiME-<ver>.zip         : Google 日本語入力用 (UTF-8, LF)
      - DMiME-<ver>-msime.zip   : Microsoft IME 用 (UTF-16 LE BOM, CRLF)
      - DMiME-<ver> igakujisho for icloud.plist : Mac ユーザ辞書用
    """
    dist.mkdir(parents=True, exist_ok=True)
    suffix = f"-{version}" if version else ""
    google_txt_name = f"DMiME{suffix}.txt"
    google_zip_path = dist / f"DMiME{suffix}.zip"
    msime_txt_name = f"DMiME{suffix}.txt"
    msime_zip_path = dist / f"DMiME{suffix}-msime.zip"
    msime_tmp = dist / f"_DMiME{suffix}-msime.txt"
    mac_plist_path = dist / f"DMiME{suffix} igakujisho for icloud.plist"

    with zipfile.ZipFile(google_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(WIN_OUT, arcname=google_txt_name)
    print(f"wrote {google_zip_path} (contains {google_txt_name})")

    n_ms = write_msime(rows, msime_tmp)
    with zipfile.ZipFile(msime_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(msime_tmp, arcname=msime_txt_name)
    msime_tmp.unlink()
    print(f"wrote {msime_zip_path} (contains {msime_txt_name}, {n_ms} entries)")

    mac_plist_path.write_bytes(MAC_OUT.read_bytes())
    print(f"wrote {mac_plist_path}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dist", type=Path, default=None,
                    help="write Release assets to this directory")
    ap.add_argument("--version", default=None,
                    help="version to embed in release asset filenames (e.g. 1.2)")
    args = ap.parse_args()

    rows = load_entries()

    n_win = write_win(rows, WIN_OUT)
    n_mac = write_mac(rows, MAC_OUT)
    print(f"wrote {WIN_OUT.relative_to(REPO)}: {n_win} entries")
    print(f"wrote {MAC_OUT.relative_to(REPO)}: {n_mac} entries")

    if args.dist:
        build_release_assets(args.dist, args.version, rows)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
