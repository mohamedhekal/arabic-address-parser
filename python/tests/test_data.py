from arabic_address_parser import parser
from arabic_address_parser._data import DATA


def test_no_alias_collisions():
    # Two different places must never share a normalized alias; pick a more specific alias instead.
    assert parser.COLLISIONS == []


def test_places_reference_existing_regions():
    ids = {r["id"] for r in DATA["regions"]}
    assert all(p["region"] in ids for p in DATA["places"])
    assert all(r["country"] in {c["code"] for c in DATA["countries"]} for r in DATA["regions"])


def test_egypt_has_all_27_governorates():
    assert sum(1 for r in DATA["regions"] if r["country"] == "EG") == 27


def test_keywords_are_not_gazetteer_names():
    clash = parser.ALL_KEYWORDS & set(parser.INDEX)
    assert clash == set(), clash


def test_every_entry_resolves_from_its_own_canonical_names():
    for p in DATA["places"]:
        assert parser.INDEX[parser.key(p["name_ar"])]["name_ar"] == p["name_ar"]
        assert parser.INDEX[parser.key(p["name_en"])]["name_ar"] == p["name_ar"]
