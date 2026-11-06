# Roadmap and starter tasks

Good first issues (no deep knowledge needed):

* Add Egyptian districts and cities for one governorate (Sohag, Qena, Aswan, Minya ... each has gaps). `data/places.txt`
* Add Franco-Arabic aliases for places that only have English or Arabic names. `data/places.txt`
* Add Saudi districts for Riyadh, Jeddah and Dammam; UAE neighbourhoods; Kuwait areas. `data/places.txt`
* Add 20 real-looking addresses in your own dialect or city to `scripts/make_cases.py` and report the ones that parse badly.

Medium:

* Fuzzy matching of typos (one edit) for gazetteer names, flagged in `resolved` and lowering confidence.
* Compound names with a number: `الحي السابع`, `المجاورة الثانية`, `الحي الأول` as structured sub-components for new cities.
* Egyptian addresses written as `المنطقة / الشارع / رقم` in reverse order.
* Better handling of `تقاطع X مع Y` (intersections) as two streets.
* A `--json-lines` CLI mode for batch files.

Larger:

* Levant (Jordan, Lebanon, Syria, Iraq, Palestine) and Maghreb (Morocco, Algeria, Tunisia, Libya) coverage.
* Additional language packages (TypeScript types are shipped; Go, PHP and Ruby ports can reuse `spec/cases`).
* Publish to PyPI and npm, add a versioned data release.
* A small playground web page.
