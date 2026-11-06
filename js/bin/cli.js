#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { formatAddress, parse, similarity, version } from "../src/index.js";

const args = process.argv.slice(2);
const opts = { defaultCountry: null, format: null, compare: null };
const words = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--default-country") opts.defaultCountry = args[++i];
  else if (a === "--format") opts.format = args[++i];
  else if (a === "--compare") opts.compare = args[++i];
  else if (a === "--version") {
    console.log(version);
    process.exit(0);
  } else if (a === "--help" || a === "-h") {
    console.log('usage: arabic-address-parser [--default-country EG] [--format ar|en] [--compare OTHER] "address text"');
    process.exit(0);
  } else words.push(a);
}
const text = words.length ? words.join(" ") : readFileSync(0, "utf8");
if (opts.compare !== null) console.log(similarity(text, opts.compare));
else {
  const result = parse(text, { defaultCountry: opts.defaultCountry });
  console.log(opts.format ? formatAddress(result, opts.format) : JSON.stringify(result, null, 2));
}
