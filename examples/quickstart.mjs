// Run from the repo root: node examples/quickstart.mjs
import { formatAddress, isSameAddress, parse } from "../js/src/index.js";

const orders = [
  "15 شارع التحرير الدقي الجيزة",
  "١٥ ش التحرير، الدقي، الجيزه",
  "شارع 9 المعادي القاهرة الدور الثالث شقة 12 بجوار مسجد الرحمن 01012345678",
];
for (const text of orders) {
  const r = parse(text, { defaultCountry: "EG" });
  console.log(`${r.confidence.toFixed(2)}  ${formatAddress(r)}`);
}
console.log("duplicate?", isSameAddress(orders[0], orders[1]));
