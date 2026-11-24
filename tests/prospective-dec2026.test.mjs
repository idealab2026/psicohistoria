import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {webcrypto} from "node:crypto";
import {verifyDEC2026,filterDEC2026,renderDEC2026} from "../src/prospective-dec2026.mjs";
if(!globalThis.crypto)Object.defineProperty(globalThis,"crypto",{value:webcrypto});
const read=name=>readFileSync(new URL("../data/"+name,import.meta.url),"utf8");
const raw=read("forecast-dec2026-pilot.json"), receipt=JSON.parse(read("forecast-dec2026-pilot-manifest.json")), countries=JSON.parse(read("forecast-2027-ucdp261.json")).countries;
test("authenticates all eight frozen cells and 196 country identities",async()=>{
 const d=await verifyDEC2026(raw,receipt,countries);
 assert.equal(d.data.cells.length,8);assert.equal(d.names.size,196);
 assert.equal(d.data.cells.reduce((n,c)=>n+c.n_eligible,0),1304);
 const f=filterDEC2026(d);
 assert.equal(f.cell.n_eligible,164);assert.equal(f.total,164);
 assert.equal(f.rows[0].country_id,640);assert.equal(f.rows[0].probability,.112502075835);
 assert.ok(f.above<5&&f.above+f.tied>=5);
 assert.equal(f.slots,5-f.above);
});
test("rejects byte mutation, false resolution and wrong country IDs",async()=>{
 await assert.rejects(verifyDEC2026(raw+" ",receipt,countries));
 await assert.rejects(verifyDEC2026(raw,{...receipt,outcomes_resolved:1},countries));
 await assert.rejects(verifyDEC2026(raw,receipt,countries.map((c,i)=>i===0?{...c,country_id:99999}:c)));
});
test("filters, pagination and excluded states preserve values",async()=>{
 const d=await verifyDEC2026(raw,receipt,countries);
 const f=filterDEC2026(d,{threshold:1,horizon:30,model:"global",includeExcluded:true,page:99});
 assert.equal(f.total,196);assert.equal(f.page,9);
 assert.ok(f.rows.every(x=>x.probability===null));
 const q=filterDEC2026(d,{query:"640"});
 assert.equal(q.total,1);assert.equal(q.rows[0].probability,.112502075835);
 assert.throws(()=>filterDEC2026(d,{model:"bad"}));
 assert.match(renderDEC2026(d),/Sin resolver/);
 assert.match(renderDEC2026(null),/no disponible o sin verificar/);
 assert.doesNotMatch(renderDEC2026(null),/7\.824/);
});
