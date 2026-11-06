#!/usr/bin/env python3
"""Fuzz the Python and JavaScript implementations against each other.

Generates random address-like strings from a pool of realistic fragments and asserts both packages return
identical output for parse(), key(), and similarity(). Exit code 1 on the first mismatch batch.
Usage: python3 scripts/parity_check.py [count] [seed]
"""
import json, pathlib, random, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python" / "src"))
from arabic_address_parser import key, parse, similarity  # noqa: E402

POOL = [
    "شارع", "ش", "ش.", "طريق", "ميدان", "كورنيش", "عمارة", "برج", "فيلا", "مبنى", "بناية", "الدور", "دور", "شقة", "وحدة", "قطعة", "مجمع",
    "حي", "منطقة", "مدينة", "قسم", "مركز", "بجوار", "بجانب", "بالقرب من", "امام", "خلف", "رقم", "محافظة",
    "التحرير", "الجمهورية", "مصطفى النحاس", "٢٥", "15", "9", "12أ", "5/3", "٣", "الثالث", "الاول", "الارضي",
    "الدقي", "المعادي", "مدينة نصر", "التجمع الخامس", "6 اكتوبر", "الشيخ زايد", "سموحة", "المنصورة", "طنطا", "بنها", "الغردقة",
    "القاهرة", "الجيزة", "الاسكندرية", "الدقهلية", "الغربية", "الرياض", "جدة", "دبي", "الكويت", "الدوحة", "المنامة", "مسقط", "مصر", "السعودية",
    "Street", "St", "Road", "Tahrir", "el", "el tahrir", "share3", "Dokki", "Maadi", "Giza", "Cairo", "Alexandria", "Building", "Floor", "Flat", "Block",
    "01012345678", "+201001234567", "12345", "ص.ب 11371", "الرمز البريدي 12345", "RRRD2929", "tel", "موبايل",
    ",", "،", "-", " - ", "\n", "|", ";", "(", ")", ".", "عبد الله", "ال", "ه", "ـ", "ً", "الله", "&", "x", "٠١٢",
]


def sample(rng):
    return " ".join(rng.choice(POOL) for _ in range(rng.randint(1, 9)))


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1234)
    texts = [sample(rng) for _ in range(count)]
    pairs = [[sample(rng), sample(rng)] for _ in range(count // 5)]
    expected = {
        "parse": [parse(t) for t in texts],
        "key": [key(t) for t in texts],
        "similarity": [similarity(a, b) for a, b in pairs],
    }
    runner = r"""
import { readFileSync } from "node:fs";
import { parse, key, similarity } from "%s/js/src/index.js";
const { texts, pairs } = JSON.parse(readFileSync(process.argv[2], "utf8"));
process.stdout.write(JSON.stringify({ parse: texts.map((t) => parse(t)), key: texts.map((t) => key(t)), similarity: pairs.map(([a, b]) => similarity(a, b)) }));
""" % ROOT
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / "in.json").write_text(json.dumps({"texts": texts, "pairs": pairs}, ensure_ascii=False), encoding="utf-8")
        (d / "run.mjs").write_text(runner, encoding="utf-8")
        out = subprocess.run(["node", str(d / "run.mjs"), str(d / "in.json")], capture_output=True, text=True, check=True).stdout
    got = json.loads(out)
    bad = 0
    for name, items in (("parse", texts), ("key", texts), ("similarity", pairs)):
        for item, e, g in zip(items, expected[name], got[name]):
            if json.loads(json.dumps(e)) != g:
                bad += 1
                if bad <= 5:
                    print(f"MISMATCH in {name}: {item!r}\n  python: {e}\n  js:     {g}")
    total = len(texts) * 2 + len(pairs)
    print(f"checked {total} outputs, {bad} mismatches")
    sys.exit(1 if bad else 0)


main()
