import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {researchOrbs,scenarioBranches,stateTransitionDiagram,domainGraph} from "../src/visuals.mjs";
const demo=JSON.parse(readFileSync(new URL("../data/demo.json",import.meta.url),"utf8"));
const registry=JSON.parse(readFileSync(new URL("../data/research.json",import.meta.url),"utf8"));
test("Orbs represent all four institutional programmes and real navigation targets",()=>{
 const out=researchOrbs(demo.programs,"P1");
 assert.equal((out.match(/class="orb-node /g)||[]).length,4);
 for(const p of demo.programs)assert.ok(out.includes('data-value="'+p.id+'"'));
 assert.match(out,/aria-pressed="true"/);
 assert.doesNotMatch(out,/private account|personal|published forecast/i);
});
test("Conceptual scenarios are interactive, annotated, and reject invented weights",()=>{
 const out=scenarioBranches(demo.branches,"B-02");
 assert.equal((out.match(/class="scenario-leaf /g)||[]).length,3);
 assert.match(out,/data-action="scenario"/);
 assert.match(out,/DEMOSTRACIÓN/);
 assert.equal(scenarioBranches(demo.branches.map((b,i)=>i?b:{...b,weight:.7}),"B-02"),"");
});
test("Only legal four-state edges are shown with no synthetic forecast disguised as observed",()=>{
 for(const [code,expected] of [["00",["00","01"]],["01",["10","11"]],["10",["00","01"]],["11",["10","11"]]]){
  const html=stateTransitionDiagram(code);
  const dest=html.split('class="state-next"')[1];
  assert.equal((dest.match(/class="state-destination"/g)||[]).length,2);
  for(const to of expected)assert.ok(dest.includes(to+" · "));
  assert.match(html,/SIN PARÁMETROS REALES/);
 }
 assert.ok(stateTransitionDiagram("<script>").includes('00 · Bajo'));
});
test("Seven institutional sources produce a filterable graph without copying research data",()=>{
 const html=domainGraph(registry.programs,"Geopolítica");
 assert.equal((html.match(/class="domain-node /g)||[]).length,7);
 assert.match(html,/data-action="registry-filter"/);
 for(const p of registry.programs)assert.ok(html.includes(p.id));
 assert.equal(domainGraph(registry.programs.slice(1)),"");
});
test("External source and label text cannot inject HTML scripts",()=>{
 const nasty=structuredClone(demo.programs);
 nasty[0].name='<img src=x onerror=alert(1)>';
 const html=researchOrbs(nasty,nasty[0].id);
 assert.doesNotMatch(html,/<img/);
 assert.match(html,/&lt;img/);
});
test("Public app integrates components without external identity or private register",()=>{
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 for(const fn of ["scientificNeuralPanel(","renderHistoricalTree(","domainGraph("])assert.ok(site.includes(fn),fn);
 const audit=readFileSync(new URL("../scripts/audit_public.py",import.meta.url),"utf8");
 assert.match(audit,/src\/visuals\.mjs/);
});
