import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {verify,brier,score,calibration} from "../src/metrics.mjs";
const data=JSON.parse(readFileSync(new URL("../data/demo.json",import.meta.url),"utf8"));
test("Synthetic data is mandatory",()=>{assert.equal(verify(data),true);assert.throws(()=>verify({...data,meta:{data_class:"observed"}}));});
test("Brier score arithmetic",()=>{assert.equal(brier([0,1],[0,1]),0);assert.ok(Math.abs(brier([.5,.5],[0,1])-.25)<1e-10);});
test("Comparable baseline and fixed evaluation size",()=>{const m=score(data.studies[0]);assert.equal(m.n,6);assert.ok(m.brier>=0&&m.brier<=1);assert.ok(m.baselineBrier>0);assert.equal(calibration(data.studies[0]).length,6);});
test("Scenario weights sum to one",()=>assert.ok(Math.abs(data.branches.reduce((a,b)=>a+b.weight,0)-1)<1e-10));
test("Reject inconsistent evidence and weights",()=>{const s={...data.studies[0],outcomes:[1]};assert.throws(()=>verify({...data,studies:[s,...data.studies.slice(1)]}));assert.throws(()=>verify({...data,branches:[{...data.branches[0],weight:.6},...data.branches.slice(1)]}));});

test("Todas las nueve vistas tienen ruta pública",()=>{
 const app=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 for(const page of ["brief","futures","shadow2027","overview","science","operations","roadmap","ideas","video"]){
  assert.ok(app.includes('"'+page+'"'),page);
 }
 assert.match(app,/history.pushState/);
 assert.match(app,/popstate/);
});
test("El registro público contiene solo muestras ilustrativas",()=>{
 assert.equal(data.meta.data_class,"synthetic");
 assert.equal(data.programs.length,4);
 assert.ok(data.milestones.every(p=>["verificado","pendiente","bloqueado"].includes(p.state)));
 assert.ok(data.ideas.every(x=>x.links.every(id=>data.programs.some(p=>p.id===id))));
});
