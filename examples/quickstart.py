"""Run from the repo root after `pip install ./python`, or with PYTHONPATH=python/src."""
from arabic_address_parser import format_address, is_same_address, parse

orders = [
    "15 شارع التحرير الدقي الجيزة",
    "١٥ ش التحرير، الدقي، الجيزه",
    "شارع 9 المعادي القاهرة الدور الثالث شقة 12 بجوار مسجد الرحمن 01012345678",
]
for text in orders:
    r = parse(text, default_country="EG")
    print(f"{r['confidence']:.2f}  {format_address(r)}")

print("duplicate?", is_same_address(orders[0], orders[1]))
