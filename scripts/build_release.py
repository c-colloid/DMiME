#!/usr/bin/env python3
# DMiME - 医学医療用語変換辞書
# Copyright (C) 2016 Kmm, Project DMiME
# Licensed under GPL-2.0-or-later

"""Build IME dictionaries (Google / MS IME / Mac) from the unified src/*.tsv.

`src/*.tsv` is the only source of truth for the dictionary. This script
materialises the shipped single-file formats on demand — it is invoked
locally by contributors who want to inspect or test output, and by
build-release.yml when a v* tag is pushed.

The build outputs are **not checked into git** (see .gitignore). They
are generated fresh each time and distributed exclusively through
GitHub Releases; avoiding committed build artifacts eliminates the
possibility of accidentally editing a generated file and having the
edit silently overwritten by CI.

Usage:
    python3 scripts/build_release.py
    python3 scripts/build_release.py --dist=dist/ --version=1.2

Without --dist the version-less living files are written to the
working tree (git-ignored):
    GoogleIME/DMiME.txt      Google 日本語入力 format (UTF-8, LF)
    WindowsIME/DMiME.txt     Microsoft IME format (UTF-16 LE BOM, CRLF)
    Mac/DMiME igakujisho for icloud.plist

With --dist the same contents are zipped into versioned release assets:
    dist/DMiME-{version}.zip                           (Google 日本語入力用)
    dist/DMiME-{version}-msime.zip                     (Microsoft IME 用)
    dist/DMiME-{version} igakujisho for icloud.plist   (Mac ユーザ辞書用)

The MS IME file is UTF-16 LE with BOM + CRLF line endings and has the
Google-specific POS tag "サジェストのみ" stripped, since MS IME has no
equivalent concept.

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
GOOGLE_OUT = REPO / "GoogleIME" / "DMiME.txt"
MSIME_OUT = REPO / "WindowsIME" / "DMiME.txt"
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
    if platform not in ("ime", "mac", "both"):
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

    seen: dict[tuple[str, str], str] = {}
    for yomi, phrase, platform, pos in rows:
        key = (yomi, phrase)
        if key in seen:
            raise SystemExit(
                f"duplicate entry {key!r}: appears with both "
                f"{seen[key]!r} and {pos!r} (or in multiple src files). "
                f"Each (yomi, phrase) pair must be unique across src/."
            )
        seen[key] = pos

    return rows


def write_google(rows: list[tuple[str, str, str, str]], path: Path) -> int:
    """Write Google 日本語入力 user dictionary (UTF-8, LF).

    Google IME accepts all POS tags used in DMiME sources verbatim.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for yomi, phrase, platform, pos in rows:
            if platform in ("ime", "both"):
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
            if platform not in ("ime", "both"):
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


def build_release_assets(dist: Path, version: str | None) -> None:
    """Zip the already-built living files into versioned release assets."""
    dist.mkdir(parents=True, exist_ok=True)
    suffix = f"-{version}" if version else ""
    google_txt_name = f"DMiME{suffix}.txt"
    msime_txt_name = f"DMiME{suffix}.txt"
    google_zip_path = dist / f"DMiME{suffix}.zip"
    msime_zip_path = dist / f"DMiME{suffix}-msime.zip"
    mac_plist_path = dist / f"DMiME{suffix} igakujisho for icloud.plist"

    with zipfile.ZipFile(google_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(GOOGLE_OUT, arcname=google_txt_name)
    print(f"wrote {google_zip_path} (contains {google_txt_name})")

    with zipfile.ZipFile(msime_zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(MSIME_OUT, arcname=msime_txt_name)
    print(f"wrote {msime_zip_path} (contains {msime_txt_name})")

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

    n_google = write_google(rows, GOOGLE_OUT)
    n_msime = write_msime(rows, MSIME_OUT)
    n_mac = write_mac(rows, MAC_OUT)
    print(f"wrote {GOOGLE_OUT.relative_to(REPO)}: {n_google} entries")
    print(f"wrote {MSIME_OUT.relative_to(REPO)}: {n_msime} entries")
    print(f"wrote {MAC_OUT.relative_to(REPO)}: {n_mac} entries")

    if args.dist:
        build_release_assets(args.dist, args.version)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
