import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {validateProjectCatalog,loadProjectCatalog} from "../src/project-catalog.mjs";
const fixture=JSON.parse(await readFile(new URL("../data/projects.json",import.meta.url)));
const clone=()=>structuredClone(fixture);
test("Institutional projection preserves exactly 4 tracks, 3 applications, 9 projects, 8 documentation cards and 14 relations",()=>{
 const data=validateProjectCatalog(clone());
 assert.equal(data.projects.length,9);
 assert.equal(data.projects.filter(p=>p.category==="Vertiente").length,4);
 assert.equal(data.projects.filter(p=>p.category==="Aplicación").length,3);
 assert.equal(data.projects.filter(p=>p.documentation!==null).length,8);
 assert.equal(data.relations.length,14);
 assert.equal(data.relations.filter(x=>x.target==="ext-midas").length,1);
 assert.equal(data.forecastIssued,0);
 assert.equal(data.verifiedProspectiveResults,0);
 assert.equal(data.privacy.sourceIdsReused,false);
});
test("Loader reuses the local unauthenticated static route and preserves cancellation",async()=>{
 const signal=new AbortController().signal;
 const d=await loadProjectCatalog(async (url,opts)=>{
  assert.equal(url,"./data/projects.json");
  assert.equal(opts.cache,"no-store");
  assert.equal(opts.credentials,"omit");
  assert.equal(opts.signal,signal);
  return {ok:true,json:async()=>clone()};
 },signal);
 assert.equal(d.status,"PUBLIC_INSTITUTIONAL_PROJECTION");
 await assert.rejects(loadProjectCatalog(async()=>({ok:false})),/UNAVAILABLE/);
});
test("Missing project, missing application, unknown external target, relations or duplicate IDs fail closed",()=>{
 const mutations=[
  x=>x.projects.pop(),
  x=>x.projects.splice(3,1),
  x=>x.projects[1].id=x.projects[0].id,
  x=>x.relations.pop(),
  x=>x.relations[0].target="unresolved",
  x=>x.relations[0].source="missing",
  x=>x.externalReferences=[],
  x=>x.coverage.projects=8,
  x=>x.projects[5].documentation=null,
  x=>x.projects[0].category="Aplicación",
  x=>x.forecastIssued=1,
  x=>x.projects[1].liveOperationalVerification=true,
  x=>x.relations[12].target="lab-core",
  x=>x.privacy.sourceIdsReused=true
 ];
 for(const mutate of mutations){
  const d=clone();mutate(d);
  assert.throws(()=>validateProjectCatalog(d),/PUBLIC_PROJECT_/);
 }
});
test("Publish gate rejects personal paths, old source identifiers and linkable archival details",()=>{
 const samples=[
  "https://github.com/another-account/source-repo",
  "user@example.com",
  "/Users/hidden/local/source",
  "PR #123",
  "/research/source-note",
  "private.host.workers.dev",
  "operator@unknown.test",
  "https://example.com/unreviewed"
 ];
 for(const value of samples){
  const d=clone();d.projects[0].stageNote=value;
  assert.throws(()=>validateProjectCatalog(d),/PUBLIC_PROJECT_PRIVACY_REJECTED/);
 }
});
test("Public page references source by code and does not publish the private raw document",async()=>{
 const site=await readFile(new URL("../src/site.mjs",import.meta.url),"utf8");
 const index=await readFile(new URL("../index.html",import.meta.url),"utf8");
 for(const required of [
  'loadProjectCatalog','function renderProjectCatalog()','state.projectCatalog',
  'project-details','catalogue-project', 'project-select',
  'Ideas y aplicaciones','PUBLIC_INSTITUTIONAL_PROJECTION'
 ])assert.ok(site.includes(required),"missing "+required);
 assert.ok(index.includes('data-section="create"'));
 assert.ok(!index.includes("legacy-internal-source"));
});
