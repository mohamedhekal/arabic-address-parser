#!/usr/bin/env python3
"""Regenerate spec/cases/parse.json from the Python implementation.

The inputs below are hand-written; the expected output is a snapshot of the Python parser that a human reviewed.
Run it, read `git diff spec/cases/parse.json`, and commit only changes you agree with.
"""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python" / "src"))
from arabic_address_parser import clean, key, parse, similarity  # noqa: E402

INPUTS = [
  # Egypt: classic ordering, with and without separators
  "15 شارع التحرير الدقي الجيزة",
  "١٥ شارع التحرير، الدقي، الجيزة",
  "شارع 9 المعادي القاهرة الدور الثالث شقة 12 بجوار مسجد الرحمن",
  "٢٢ ش مصطفى النحاس، مدينة نصر، 01012345678",
  "محافظة الإسكندرية سموحة شارع فوزي معاذ عمارة 7 الدور الخامس شقة 21 بالقرب من مول سان ستيفانو",
  "مدينة نصر شارع عباس العقاد ٢٥ ص.ب 11371",
  "شارع الجمهورية - المنصورة - الدقهلية",
  "ش النصر بنها القليوبية",
  "برج القاهرة الزمالك، الدور 4",
  "ابراج النيل، كورنيش المعادي، القاهره",
  "6 اكتوبر الحي السابع المجاورة الثانية",
  "التجمع الخامس شارع التسعين عمارة 12 شقة 4 القاهرة الجديدة",
  "الشيخ زايد الحي الاول عمارة 45 الدور الارضي",
  "شارع سعد زغلول بجانب البنك الاهلي طنطا الغربية",
  "عمارة رقم 8 شارع رقم 15 حي المقطم القاهرة",
  "منطقة الهرم شارع فيصل الرئيسي بالقرب من محطة المترو الجيزة",
  "قسم اول مدينة نصر القاهرة",
  "القاهرة الدقي",
  "الجيزة المعادي",
  "شرم الشيخ خليج نعمة فندق الريتز",
  "محطة الرمل شارع صفية زغلول الاسكندرية",
  "الغردقة الدهار شارع سيجا فيلا 10 البحر الاحمر",
  # Egypt: Franco-Arabic and English
  "15 share3 el tahrir el dokki el giza",
  "Flat 12, Floor 3, 15 Tahrir St, Dokki, Giza, Egypt",
  "26th of July Road, Mohandessin, Giza",
  "Building 5, Sheikh Zayed, Giza",
  "12 ma3adi cairo",
  "villa 22 new cairo 5th settlement",
  # Gulf
  "حي النخيل، شارع الأمير سلطان، الرياض، المملكة العربية السعودية، الرمز البريدي 12345",
  "RRRD2929 الرياض",
  "حي العليا شارع التحلية جدة",
  "قطعة 3 شارع 5 جادة 2 منزل 10 السالمية الكويت",
  "مبنى 123 طريق 456 مجمع 789 المنامة البحرين",
  "Building 12 Road 5 Block 7 Manama",
  "دبي ديرة شارع الرقة بناية 5",
  "دبي مردف شارع 12 فيلا 7 الامارات",
  "Al Khalidiyah, Abu Dhabi, UAE",
  "الدوحة اللؤلؤة برج 5 الدور 12 شقة 1203",
  "مسقط السيب شارع الجامعة",
  # edge cases
  "",
  "   ",
  "ش.التحرير 15",
  "شارع التحرير\nالدقي\nالجيزة",
  "عمارة 5أ شارع الجمهورية",
  "شارع 26 يوليو الزمالك",
  "الاسكندريه",
  "tel 01234567890 cairo",
]

NORMALIZE = [
  "الإسكندرية", "اسكندريه", "٦ أكتوبر", "القَاهِرَة", "مدينة نصـــر", "Nasr   City", "  EL Tahrir  St. ", "شارع التحريييييير",
  "٠١٠١٢٣٤٥٦٧٨", "گ پ چ ڤ", "ﻻ", "مؤتمر ئ", "", "الله", "ال", "هل", "al ahram", "سموحا", "عمارة ١٥/٣",
]

SIMILARITY = [
  ["15 شارع التحرير الدقي الجيزة", "١٥ ش التحرير، الدقي، الجيزة"],
  ["15 شارع التحرير الدقي الجيزة", "17 شارع التحرير الدقي الجيزة"],
  ["شارع الجمهورية المنصورة", "شارع الجمهوريه المنصوره"],
  ["شارع الجمهورية المنصورة", "شارع سعد زغلول طنطا"],
  ["Tahrir St, Dokki, Giza", "Dokki Giza Tahrir Street"],
  ["شقة 4 عمارة 12 شارع التسعين", "شقة 5 عمارة 12 شارع التسعين"],
  ["", ""],
  ["القاهرة", ""],
]


def main():
    cases = []
    for text in INPUTS:
        r = parse(text)
        expect = {k: v for k, v in r.items() if k not in ("input", "cleaned", "resolved") and v not in (None, [], "")}
        cases.append({"input": text, "expect": expect})
    (ROOT / "spec" / "cases" / "normalize.json").write_text(
        json.dumps([{"input": t, "clean": clean(t), "key": key(t)} for t in NORMALIZE], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "spec" / "cases" / "similarity.json").write_text(
        json.dumps([{"a": a, "b": b, "score": similarity(a, b)} for a, b in SIMILARITY], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out = ROOT / "spec" / "cases" / "parse.json"
    out.write_text(json.dumps(cases, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for t in NORMALIZE:
        print("norm", repr(t), "->", repr(clean(t)), "|", repr(key(t)))
    for a, b in SIMILARITY:
        print("sim", repr(a), repr(b), similarity(a, b))
    for c in cases[:0]:
        e = {k: v for k, v in c["expect"].items() if k not in ("normalized", "language")}
        print(repr(c["input"]), "\n   ", e)

main()
