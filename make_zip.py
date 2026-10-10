#!/usr/bin/env python3
"""Builds stop-glazing-me.zip for the Claude app: the skill folder at the root of the zip."""
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL = ROOT / "skills" / "stop-glazing-me"
OUT = ROOT / "stop-glazing-me.zip"
FIXED_TIME = (2026, 10, 9, 0, 0, 0)  # same bytes every build


def build(out: Path = OUT) -> Path:
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(SKILL.rglob("*")):
            if path.is_file() and path.name != ".DS_Store":
                info = zipfile.ZipInfo(f"stop-glazing-me/{path.relative_to(SKILL).as_posix()}", FIXED_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
    return out


if __name__ == "__main__":
    print(build())
