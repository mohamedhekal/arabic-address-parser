"""Run the language-independent cases in spec/cases/ (shared with the JavaScript package)."""
import json
import pathlib

import pytest

from arabic_address_parser import clean, key, parse, similarity

CASES = pathlib.Path(__file__).resolve().parents[2] / "spec" / "cases"


def load(name):
    return json.loads((CASES / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", load("parse.json"), ids=lambda c: c["input"][:40] or "<empty>")
def test_parse_cases(case):
    result = parse(case["input"])
    actual = {k: v for k, v in result.items() if k not in ("input", "cleaned", "resolved") and v not in (None, [], "")}
    assert actual == case["expect"]


@pytest.mark.parametrize("case", load("normalize.json"), ids=lambda c: c["input"][:30] or "<empty>")
def test_normalize_cases(case):
    assert clean(case["input"]) == case["clean"]
    assert key(case["input"]) == case["key"]


@pytest.mark.parametrize("case", load("similarity.json"), ids=lambda c: c["a"][:25] + "~" + c["b"][:25])
def test_similarity_cases(case):
    assert similarity(case["a"], case["b"]) == case["score"]
