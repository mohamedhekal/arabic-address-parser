import assert from "node:assert/strict";
import test from "node:test";
import { COLLISIONS, ALL_KEYWORDS, INDEX } from "../src/parser.js";
import { formatAddress, isSameAddress, key, parse, similarity } from "../src/index.js";

test("orthographic variants share a key", () => {
  for (const [a, b] of [["الإسكندرية", "اسكندريه"], ["القاهرة", "القاهره"], ["٦ أكتوبر", "6 اكتوبر"], ["سموحة", "سموحه"], ["المعادي", "معادى"], ["مدينة نصر", "مدينه نصر"]]) {
    assert.equal(key(a), key(b), `${a} vs ${b}`);
  }
  assert.notEqual(key("سموحة"), key("المعادي"));
});

test("Abdullah keeps its article; digits and diacritics are cleaned", () => {
  assert.equal(key("عبد الله"), "عبد الله");
  assert.equal(key("شارع ١٥ القَاهِرَة"), "شارع 15 قاهره");
});

test("null and empty input", () => {
  assert.equal(key(null), "");
  assert.equal(parse(null).confidence, 0);
  assert.deepEqual(parse("").unparsed, []);
});

test("every spelling resolves to the same region", () => {
  const spellings = ["الاسكندريه", "الإسكندرية", "اسكندرية", "Alexandria", "eskandariya", "alex"];
  assert.deepEqual(new Set(spellings.map((s) => parse(s).region)), new Set(["الإسكندرية"]));
});

test("region inference, warnings and default country", () => {
  const r = parse("المعادي");
  assert.equal(r.region, "القاهرة");
  assert.equal(r.resolved.region.inferred, true);
  assert.deepEqual(parse("الدقي القاهرة").warnings, ["region_mismatch:الدقي"]);
  assert.equal(parse("شارع النصر", { defaultCountry: "EG" }).country_code, "EG");
  assert.equal(parse("شارع النصر").country_code, null);
  assert.equal(parse("شارع النصر الرياض", { defaultCountry: "EG" }).country_code, "SA");
});

test("street named like a district; landmark tail; floors; phones", () => {
  const a = parse("شارع الهرم الجيزة");
  assert.equal(a.street, "شارع الهرم");
  assert.equal(a.district, null);
  const b = parse("شارع سعد زغلول بجانب البنك الاهلي طنطا الغربية");
  assert.equal(b.landmark, "بجانب البنك الاهلي");
  assert.equal(b.region, "الغربية");
  assert.equal(parse("الدور الثالث").floor, 3);
  assert.equal(parse("الدور الارضي").floor, 0);
  assert.equal(parse("شارع النصر 01001234567").phone, "01001234567");
  assert.equal(parse("عمارة 12345").phone, null);
});

test("similarity and format", () => {
  const a = "15 شارع التحرير الدقي الجيزة";
  assert.equal(similarity(a, a), 1);
  assert.ok(similarity(a, "17 شارع التحرير الدقي الجيزة") < 0.85);
  assert.ok(isSameAddress(a, "15 شارع التحرير، الدقي، الجيزه"));
  assert.equal(formatAddress(parse(a)), "15 شارع التحرير، الدقي، الجيزة، مصر");
  assert.equal(formatAddress(parse(a), "en"), "15 شارع التحرير, Dokki, Giza, Egypt");
});

test("data integrity", () => {
  assert.deepEqual(COLLISIONS, []);
  for (const k of ALL_KEYWORDS) assert.equal(INDEX.has(k), false, `keyword ${k} is also a place name`);
});
