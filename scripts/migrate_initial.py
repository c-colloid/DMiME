#!/usr/bin/env python3
# DMiME - 医学医療用語変換辞書
# Copyright (C) 2016 Kmm, Project DMiME
# Licensed under GPL-2.0-or-later

"""One-time migration: existing Win TSV and Mac plist -> unified src/*.tsv.

Merges the two historical dictionary files into a single set of sources
partitioned by 50音 bucket, annotating each entry with a platform tag
(`win` / `mac` / `both`) and preserving part-of-speech from the Win side
where available.

Usage:
    python3 scripts/migrate_initial.py           # write src/*.tsv
    python3 scripts/migrate_initial.py --verify  # only report summary, no writes
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _buckets import BUCKET_ORDER, bucket_for  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WIN_SRC = REPO / "WindowsIME" / "DMiME-1.1.txt"
MAC_SRC = REPO / "Mac" / "DMiME1.1 igakujisho for icloud.plist"
OUT_DIR = REPO / "src"

PLIST_ENTRY = re.compile(
    r"<dict><key>shortcut</key><string>([^<]*)</string>"
    r"<key>phrase</key><string>([^<]*)</string></dict>"
)


def read_win(path: Path) -> dict[tuple[str, str], str]:
    """Return {(yomi, phrase): pos} from the Windows TSV."""
    out: dict[tuple[str, str], str] = {}
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            yomi, phrase = parts[0], parts[1]
            pos = parts[2] if len(parts) >= 3 and parts[2] else "名詞"
            out[(yomi, phrase)] = pos
    return out


def read_mac(path: Path) -> set[tuple[str, str]]:
    entries: set[tuple[str, str]] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            m = PLIST_ENTRY.search(line)
            if m:
                entries.add((m.group(1), m.group(2)))
    return entries


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="report stats without writing src/")
    args = ap.parse_args()

    win = read_win(WIN_SRC)
    mac = read_mac(MAC_SRC)
    win_keys = set(win.keys())

    both = win_keys & mac
    only_win = win_keys - mac
    only_mac = mac - win_keys

    print(f"Win entries: {len(win_keys)}")
    print(f"Mac entries: {len(mac)} (unique)")
    print(f"  both: {len(both)}")
    print(f"  win-only: {len(only_win)}")
    print(f"  mac-only: {len(only_mac)}")

    buckets: dict[str, list[tuple[str, str, str, str]]] = defaultdict(list)

    for key in win_keys | mac:
        yomi, phrase = key
        if key in both:
            platform = "both"
        elif key in only_win:
            platform = "win"
        else:
            platform = "mac"
        pos = win.get(key, "名詞")
        buckets[bucket_for(yomi)].append((yomi, phrase, platform, pos))

    for name in BUCKET_ORDER:
        buckets[name].sort(key=lambda r: (r[0], r[1]))

    if args.verify:
        total = sum(len(v) for v in buckets.values())
        print(f"\nTotal unique entries: {total}")
        for name in BUCKET_ORDER:
            n = len(buckets[name])
            print(f"  {name:<8} {n:>6} entries")
        return 0

    OUT_DIR.mkdir(exist_ok=True)
    for name in BUCKET_ORDER:
        path = OUT_DIR / f"{name}.tsv"
        with path.open("w", encoding="utf-8", newline="\n") as f:
            for yomi, phrase, platform, pos in buckets[name]:
                f.write(f"{yomi}\t{phrase}\t{platform}\t{pos}\n")
        print(f"wrote {path.relative_to(REPO)}: {len(buckets[name])} entries")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
