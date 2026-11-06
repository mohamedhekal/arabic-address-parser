#!/usr/bin/env python3
"""Compile data/places.txt + data/keywords.json into the generated modules
python/src/arabic_address_parser/_data.py and js/src/data.js.

Run:  python3 scripts/sync_data.py          (rewrite files)
      python3 scripts/sync_data.py --check  (exit 1 if generated files are stale; used by CI)
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
HEADER = "GENERATED FILE - edit data/ and run scripts/sync_data.py"


def load():
    countries, regions, places = [], [], []
    for n, line in enumerate((ROOT / "data" / "places.txt").read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        f = line.split("|")
        kind = f[0]
        if kind == "C" and len(f) == 5:
            countries.append({"code": f[1], "name_ar": f[2], "name_en": f[3], "aliases": [a for a in f[4].split(";") if a]})
        elif kind == "R" and len(f) == 6:
            regions.append({"id": f[1], "country": f[2], "name_ar": f[3], "name_en": f[4], "aliases": [a for a in f[5].split(";") if a]})
        elif kind == "P" and len(f) == 6:
            if f[1] not in ("city", "district"):
                raise SystemExit(f"places.txt:{n}: unknown place type {f[1]!r}")
            places.append({"type": f[1], "region": f[2], "name_ar": f[3], "name_en": f[4], "aliases": [a for a in f[5].split(";") if a]})
        else:
            raise SystemExit(f"places.txt:{n}: malformed line: {line!r}")
    region_ids = {r["id"] for r in regions}
    for p in places:
        if p["region"] not in region_ids:
            raise SystemExit(f"unknown region id {p['region']!r} for place {p['name_ar']}")
    keywords = json.loads((ROOT / "data" / "keywords.json").read_text(encoding="utf-8"))
    keywords.pop("_comment", None)
    return {"countries": countries, "regions": regions, "places": places, "keywords": keywords}


def render_py(data):
    body = json.dumps(data, ensure_ascii=False, indent=1)
    return f'# {HEADER}\nimport json as _json\n\nDATA = _json.loads(r"""{body}""")\n'


def render_js(data):
    body = json.dumps(data, ensure_ascii=False, indent=1)
    return f"// {HEADER}\nexport default {body};\n"


def main():
    data = load()
    outputs = {
        ROOT / "python/src/arabic_address_parser/_data.py": render_py(data),
        ROOT / "js/src/data.js": render_js(data),
    }
    if "--check" in sys.argv:
        stale = [str(p.relative_to(ROOT)) for p, text in outputs.items() if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("stale generated files:", *stale, sep="\n  ")
            sys.exit(1)
        print("generated data is up to date")
        return
    for p, text in outputs.items():
        p.write_text(text, encoding="utf-8")
        print("wrote", p.relative_to(ROOT))
    print(f"{len(data['countries'])} countries, {len(data['regions'])} regions, {len(data['places'])} places")


if __name__ == "__main__":
    main()
