# Contributing

Thank you for helping. Most contributions need no code.

## The easy wins

**Add or fix a place** (`data/places.txt`, one line each):

```text
P|district|EG-C|المعادي|Maadi|ma3adi;ma3ady;el maadi
```

Format: `P|type|region_id|name_ar|name_en|aliases`. `type` is `city` or `district`. The canonical names are indexed automatically;
`aliases` (separated by `;`) are extra spellings, including Franco-Arabic. Aliases must be unique across the whole file: if two places could
share a spelling, leave that spelling out. Regions are `R|...` lines and countries `C|...` lines, described at the top of the file.

**Add a test address** to `INPUTS` in `scripts/make_cases.py`, run it, and read the diff of `spec/cases/parse.json`.
If the result is wrong, that is a bug report you can fix or file.

## Workflow

```bash
python3 scripts/sync_data.py                       # after editing data/
python3 scripts/make_cases.py                      # after adding cases; review the diff
cd python && pip install -e '.[test]' && pytest    # Python tests
cd ../js && npm test                               # JavaScript tests
python3 scripts/parity_check.py                    # both languages must agree
```

CI runs the same steps and fails if the generated files (`python/.../_data.py`, `js/src/data.js`) are out of date.

## Changing parser behaviour

1. Change `spec/SPEC.md` first (or in the same pull request), explaining the rule.
2. Implement it in **both** `python/` and `js/`, in the same shape, so the two stay easy to compare.
3. Add inputs to `scripts/make_cases.py` that show the new behaviour and regenerate the cases.
4. Run `parity_check.py`.

Prefer rules that fail safe: unrecognized text should land in `unparsed`, never be guessed.

## Branches and commits

Short-lived branches named `<type>/<description>` (`feature/`, `fix/`, `data/`, `docs/`, `test/`), one focused pull request each,
commit messages like `feat(parser): ...` or `data(egypt): add Sohag districts`.
Pair work gets a `Co-authored-by:` trailer.

## Data and licensing

Contribute only data you may share under the MIT license. Do not copy from datasets with restrictive or share-alike licenses (including OpenStreetMap extracts
and commercial gazetteers). Place names and administrative facts you know yourself, or take from official public sources, are fine; say where in the pull request.
