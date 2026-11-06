import pytest

from arabic_address_parser import format_address, is_same_address, key, parse, similarity


@pytest.mark.parametrize(
    "a,b",
    [
        ("الإسكندرية", "اسكندريه"),
        ("القاهرة", "القاهره"),
        ("٦ أكتوبر", "6 اكتوبر"),
        ("سموحة", "سموحه"),
        ("المعادي", "معادى"),
        ("مدينة نصر", "مدينه نصر"),
    ],
)
def test_orthographic_variants_share_a_key(a, b):
    assert key(a) == key(b)


def test_unrelated_names_do_not_collide():
    assert key("سموحة") != key("المعادي")


def test_abdullah_keeps_its_article():
    assert key("عبد الله") == "عبد الله"


def test_digits_and_diacritics_are_cleaned():
    assert key("شارع ١٥ القَاهِرَة") == "شارع 15 قاهره"


def test_none_and_empty_input():
    assert key(None) == ""
    r = parse(None)
    assert r["confidence"] == 0.0 and r["street"] is None
    assert parse("")["unparsed"] == []


def test_every_spelling_resolves_to_the_same_region():
    spellings = ["الاسكندريه", "الإسكندرية", "اسكندرية", "Alexandria", "eskandariya", "alex"]
    assert {parse(s)["region"] for s in spellings} == {"الإسكندرية"}


def test_region_is_inferred_from_district():
    r = parse("المعادي")
    assert r["region"] == "القاهرة"
    assert r["resolved"]["region"]["inferred"] is True


def test_greater_cairo_mismatch_is_a_warning_not_an_error():
    r = parse("الدقي القاهرة")
    assert r["region"] == "القاهرة"
    assert r["warnings"] == ["region_mismatch:الدقي"]


def test_default_country_only_applies_when_nothing_else_says_otherwise():
    assert parse("شارع النصر", default_country="EG")["country_code"] == "EG"
    assert parse("شارع النصر")["country_code"] is None
    assert parse("شارع النصر الرياض", default_country="EG")["country_code"] == "SA"


def test_street_named_like_a_district_is_not_misread():
    r = parse("شارع الهرم الجيزة")
    assert r["street"] == "شارع الهرم"
    assert r["district"] is None


def test_landmark_does_not_swallow_trailing_region():
    r = parse("شارع سعد زغلول بجانب البنك الاهلي طنطا الغربية")
    assert r["landmark"] == "بجانب البنك الاهلي"
    assert r["region"] == "الغربية" and r["city"] == "طنطا"


def test_floor_words_and_digits():
    assert parse("الدور الثالث")["floor"] == 3
    assert parse("دور 7")["floor"] == 7
    assert parse("الدور الارضي")["floor"] == 0


def test_phone_numbers_are_extracted_not_confused_with_building():
    r = parse("شارع النصر 01001234567")
    assert r["phone"] == "01001234567" and r["building"] is None


def test_short_numbers_are_not_phones():
    assert parse("عمارة 12345")["phone"] is None


def test_confidence_is_bounded():
    for text in ["", "كلام عشوائي كثير جدا جدا جدا جدا جدا جدا جدا", "15 شارع التحرير الدقي الجيزة شقة 3 الدور 2"]:
        assert 0.0 <= parse(text)["confidence"] <= 1.0


def test_similarity_properties():
    a = "15 شارع التحرير الدقي الجيزة"
    assert similarity(a, a) == 1.0
    assert similarity(a, "١٥ ش التحرير الدقي الجيزة") == 1.0
    assert similarity(a, "17 شارع التحرير الدقي الجيزة") < 0.85
    assert is_same_address(a, "15 شارع التحرير، الدقي، الجيزه")
    assert not is_same_address(a, "شارع الجمهورية المنصورة")


def test_format_address_both_languages():
    r = parse("15 شارع التحرير الدقي الجيزة")
    assert format_address(r) == "15 شارع التحرير، الدقي، الجيزة، مصر"
    assert format_address(r, "en") == "15 شارع التحرير, Dokki, Giza, Egypt"
