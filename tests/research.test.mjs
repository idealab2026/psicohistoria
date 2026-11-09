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


test("priority research questions have decision-value protocols and no claimed predictive skill",()=>{
 assert.equal(registry.questions.length,10);
 assert.deepEqual(registry.questions.reduce((counts,q)=>(counts[q.priority]=(counts[q.priority]||0)+1,counts),{}),{P1:3,P2:5,P3:2});
 assert.ok(registry.questions.every(q=>q.skill_demonstrated===false));
 assert.ok(registry.questions.every(q=>q.target&&q.horizon&&q.baseline&&q.decision&&q.gate));
 const legacy=registry.questions.find(q=>q.id==="Q-GEO-02");
 assert.equal(legacy.model_status,"retrospectivo_no_prospectivo");
});
test("agenda rejects missing baselines, unsupported priorities or fabricated success",()=>{
 let changed=structuredClone(registry);
 changed.questions[0].baseline="";
 assert.throws(()=>verifyResearch(changed),/protocol/);
 changed=structuredClone(registry);
 changed.questions[1].skill_demonstrated=true;
 assert.throws(()=>verifyResearch(changed),/Premature/);
 changed=structuredClone(registry);
 changed.questions[2].priority="P0";
 assert.throws(()=>verifyResearch(changed),/priority/);
 changed=structuredClone(registry);
 changed.questions[3].program="BAD-01";
 assert.throws(()=>verifyResearch(changed),/orphan/);
});
test("question agenda is visible as an institutional research view",()=>{
 const source=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(source,/\["questions","Preguntas útiles"\]/);
 assert.match(source,/function renderUsefulQuestions\(/);
 assert.match(source,/case "question-priority"/);
 assert.match(source,/¿Qué queremos anticipar/);
 assert.match(source,/Sin validar/);
});
