import test from "node:test";
import assert from "node:assert/strict";
import {readFile,stat} from "node:fs/promises";
import {fileURLToPath} from "node:url";

const ROOT=fileURLToPath(new URL("../",import.meta.url));
const path=name=>fileURLToPath(new URL("../"+name,import.meta.url));
const ABSENT=["data/scientific-workbook.json","src/scientific-archive.mjs"];
test("Only aggregate historical counts, never source rows, enter public Pages",async()=>{
 for(const name of ABSENT){
  await assert.rejects(stat(path(name)),{code:"ENOENT"});
 }
 const code=await readFile(path("src/site.mjs"),"utf8");
 assert.doesNotMatch(code,/scientific-workbook\.json|scientificArchiveTable|verifyScientificArchive/);
 assert.match(code,/PUBLIC_RECORD_COUNTS/);
 const match=code.match(/const PUBLIC_RECORD_COUNTS=Object\.freeze\(\[([\s\S]*?)\]\);/);
 assert.ok(match,"Public aggregate inventory must remain explicit");
 const counts=[...match[1].matchAll(/\["[^"]+",(\d+)\]/g)].map(x=>Number(x[1]));
 assert.equal(counts.length,11);
 assert.equal(counts.reduce((a,b)=>a+b,0),1835);
});
test("Published package must never copy raw cells or source reader",async()=>{
 const workflow=await readFile(path(".github/workflows/pages.yml"),"utf8");
 const lines=workflow.split("\n").filter(line=>/^\s+cp /.test(line));
 assert.ok(lines.length>=3);
 for(const line of lines){
  assert.doesNotMatch(line,/scientific-workbook\.json|scientific-archive\.mjs/);
 }
 const audit=await readFile(path("scripts/audit_public.py"),"utf8");
 assert.match(audit,/BLOCKED/);
 assert.match(audit,/Private scientific source must not exist in public checkout/);
});

test("Predictive tree links to local country comparison without publishing private catalogues",async()=>{
 const site=await readFile(path("src/site.mjs"),"utf8");
 const ui=await readFile(path("trabajo.html"),"utf8");
 const controller=await readFile(path("src/country-comparison-view.mjs"),"utf8");
 assert.match(site,/renderHistoricalTree\(state\)/);
 assert.match(site,/loadPublicTree\(/);
 assert.doesNotMatch(site,/catálogo privado local/);
 assert.match(ui,/connect-src 'none'/);
 assert.match(ui,/comparison-chart/);
 const mainTree=await readFile(path("src/main-country-tree.mjs"),"utf8");
 assert.match(mainTree,/tree-country-select/);
 assert.match(mainTree,/Sociedad<select/);
 assert.doesNotMatch(mainTree,/tree-private-file|type="file"/);
 assert.match(mainTree,/no equivale a una predicción registrada/);
 assert.doesNotMatch(controller,/fetch\(|XMLHttpRequest|sendBeacon/);
});
