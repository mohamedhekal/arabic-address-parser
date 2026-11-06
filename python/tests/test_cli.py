import json

from arabic_address_parser.__main__ import main


def test_cli_json(capsys):
    assert main(["15 شارع التحرير الدقي الجيزة"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["street"] == "شارع التحرير" and out["region"] == "الجيزة"


def test_cli_format_and_compare(capsys):
    main(["--format", "en", "15 شارع التحرير الدقي الجيزة"])
    assert capsys.readouterr().out.strip() == "15 شارع التحرير, Dokki, Giza, Egypt"
    main(["--compare", "15 ش التحرير الدقي", "15 شارع التحرير الدقي"])
    assert capsys.readouterr().out.strip() == "1.0"
