#!/usr/bin/env python3
"""Place each arcade MRA below _Arcade/_Ongo/<core>/.

The core is read from the MRA's <rbf> element, so newly imported upstream
MRAs are categorised without maintaining a manually curated title list.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


ARCADE = Path("_Arcade")
DESTINATION = ARCADE / "_Ongo"


def core_name(mra: Path) -> str | None:
    try:
        root = ET.parse(mra).getroot()
        value = next(
            (
                element.text
                for element in root.iter()
                if element.tag.rsplit("}", 1)[-1] == "rbf" and element.text
            ),
            None,
        )
    except ET.ParseError:
        value = None
    if not value:
        match = re.search(r"<rbf>\s*([^<]+?)\s*</rbf>", mra.read_text(errors="replace"))
        value = match.group(1) if match else None
    if not value:
        return None
    name = Path(value.strip()).name
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name) or None


def target_for(root: Path, mra: Path, core: str) -> Path:
    relative = mra.relative_to(root / ARCADE)
    parts = relative.parts
    base = root / DESTINATION / core
    if "_alternatives" in parts:
        index = parts.index("_alternatives")
        return base / Path(*parts[index:])
    return base / mra.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", type=Path)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    arcade = root / ARCADE
    moved = skipped = 0
    for mra in sorted(arcade.rglob("*.mra")):
        core = core_name(mra)
        if not core:
            print(f"Cannot determine RBF: {mra.relative_to(root)}", file=sys.stderr)
            skipped += 1
            continue
        target = target_for(root, mra, core)
        if target == mra:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != mra.read_bytes():
                raise RuntimeError(f"Conflicting MRA target: {target.relative_to(root)}")
            mra.unlink()
        else:
            shutil.move(str(mra), target)
        moved += 1
    if args.report:
        print(f"Moved {moved} MRA files; skipped {skipped} without an <rbf> tag.")
    return 1 if skipped else 0


if __name__ == "__main__":
    raise SystemExit(main())
