import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {verifyResearch,parseForecastCSV,evaluateLocalForecast,CSV_TEMPLATE} from "../src/research.mjs";

const registry=JSON.parse(readFileSync(new URL("../data/research.json",import.meta.url),"utf8"));
test("the institutional research registry is complete and does not claim forecasting skill",()=>{
 assert.equal(verifyResearch(registry),true);
 assert.equal(registry.programs.length,7);
 assert.ok(registry.programs.every(p=>p.skill_demonstrated===false));
});
test("unknown source domains are rejected",()=>{
 const changed=structuredClone(registry);changed.programs[0].source.url="https://example.com/source";
 assert.throws(()=>verifyResearch(changed),/allowlist/);
});
test("prematurely issued forecasts are rejected",()=>{
 const changed=structuredClone(registry);changed.forecast_issued=1;
 assert.throws(()=>verifyResearch(changed),/Unverified/);
});
test("the local Brier score is correct and not verified",()=>{
 const result=evaluateLocalForecast(parseForecastCSV(CSV_TEMPLATE));
 assert.equal(result.n,2);
 assert.ok(Math.abs(result.model_brier-0.065)<1e-12);
 assert.equal(result.baseline_brier,0.25);
 assert.equal(result.verified_independently,false);
});
test("lookahead and forecasts after event start are rejected",()=>{
 const rows=parseForecastCSV(CSV_TEMPLATE);rows[0].issued_at="2024-04-01";
 assert.throws(()=>evaluateLocalForecast(rows),/Temporal/);
});
test("malformed numeric and temporal rows fail closed",()=>{
 let rows=parseForecastCSV(CSV_TEMPLATE);rows[0].model_probability="1.4";
 assert.throws(()=>evaluateLocalForecast(rows),/probability/);
 rows=parseForecastCSV(CSV_TEMPLATE);rows[0].event_end="2024-02-30";
 assert.throws(()=>evaluateLocalForecast(rows),/calendar/);
 assert.throws(()=>parseForecastCSV("a,b,c\n1,2,3"),/columns/);
});
test("formulas, text and unvalidated scientific evidence are not accepted as probabilities",()=>{
 const rows=parseForecastCSV(CSV_TEMPLATE); rows[0].model_probability="=1+0";
 assert.throws(()=>evaluateLocalForecast(rows));
});

test("Historical science archive preserves eleven tables and 1835 records without reissuing predictions",async()=>{
 const {verifyScientificArchive,scientificArchiveTable}=await import("../src/scientific-archive.mjs");
 const doc=JSON.parse(readFileSync(new URL("../data/scientific-workbook.json",import.meta.url),"utf8"));
 assert.deepEqual(verifyScientificArchive(doc),{tables:11,records:1835,predictions:1177,verifiedOutcomes:0});
 assert.equal(scientificArchiveTable(doc,{table:3}).count,1177);
 assert.equal(scientificArchiveTable(doc,{table:3}).pages,40);
 const altered=structuredClone(doc);altered.tables[3].rows.pop();assert.throws(()=>verifyScientificArchive(altered));
});
