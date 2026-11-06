// Runs the language-independent cases in spec/cases/ (shared with the Python package).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { clean, key, parse, similarity } from "../src/index.js";

const load = (name) => JSON.parse(readFileSync(new URL(`../../spec/cases/${name}`, import.meta.url), "utf8"));
const present = (v) => !(v === null || v === undefined || v === "" || (Array.isArray(v) && v.length === 0));

for (const c of load("parse.json")) {
  test(`parse: ${c.input.slice(0, 40) || "<empty>"}`, () => {
    const r = parse(c.input);
    const actual = Object.fromEntries(Object.entries(r).filter(([k, v]) => !["input", "cleaned", "resolved"].includes(k) && present(v)));
    assert.deepEqual(actual, c.expect);
  });
}
for (const c of load("normalize.json")) {
  test(`normalize: ${c.input.slice(0, 30) || "<empty>"}`, () => {
    assert.equal(clean(c.input), c.clean);
    assert.equal(key(c.input), c.key);
  });
}
for (const c of load("similarity.json")) {
  test(`similarity: ${c.a.slice(0, 25)} ~ ${c.b.slice(0, 25)}`, () => {
    assert.equal(similarity(c.a, c.b), c.score);
  });
}
