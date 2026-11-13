import test from "node:test";
import assert from "node:assert/strict";
import {
 validateProspectiveRegistry,filterProspectiveRegistry,renderProspectiveRegistry,
 COHORT_ORDER,ORIGINAL_SHA,ORIGINAL_COMMITS
} from "../src/prospective-registry.mjs";

const days={
 GEO2027:"2026-11-10T17:23:12Z",
 NEWCONF2027:"2026-11-11T10:10:21Z",
 ACD2027:"2026-11-12T22:24:56Z"
};
function fakeDoc(){
 const rows=[];
 const cohorts={};
 const prompts={
  GEO2027:"¿Se superarán 25 muertes estatales registradas de violencia organizada durante 2027?",
  NEWCONF2027:"¿Aparecerá un nuevo episodio de conflicto intraestatal durante el año 2027?",
  ACD2027:"¿Persistirá algún conflicto intraestatal registrado durante 2027 respecto a 2025?"
 };
 for(const id of COHORT_ORDER){
  const count=id==="ACD2027"?32:196;
  cohorts[id]={
   question:prompts[id],source:"UCDP "+id+" edición oficial",
   source_url:"https://ucdp.uu.se/downloads/test-"+id+".zip",
   source_sha256:"9".repeat(64),
   primary_model:id==="ACD2027"?"p_global_recent5":"p_model",
   issue_utc:days[id],first_public_commit:ORIGINAL_COMMITS[id],
   forecast_sha256:ORIGINAL_SHA[id],fixed_country_count:count,
   origin_data_through:2025,
   resolution:"PENDIENTE_FUENTE_ANUAL_OFICIAL_2027",
   evaluation:"Brier del primer corte completo oficial y los mismos países de origen."
  };
  for(let country=1;country<=count;country++){
   rows.push({
    cohort:id,country_id:country,
    country:country===41?"Haití":"País "+country,
    p_primary:.42,p_secondary:id==="GEO2027"?
      {p_global_markov:.3,p_shadow_exploratorio:.4}:
      id==="NEWCONF2027"?{p_baseline_global_5y:.2}:
      {p_country_eb_exploratorio:.6,p_lag1_group_exploratorio:.5},
    issued_status:"EMITIDA_PENDIENTE",resolved_2027:false,
    observed_2027:null,certified_result:false,
    geo_transition_alert:id==="GEO2027"&&country<=10?"ENTRADA":
      id==="GEO2027"&&country<=15?"RESOLUCION":null
   });
  }
 }
 return {
  schema:"idealab.psico.prospective_2027_issued_registry.v1",
  status:"PROSPECTIVE_ISSUED_ALL_OUTCOMES_2027_UNRESOLVED",
  target_year:2027,cohort_order:[...COHORT_ORDER],
  n_distinct_issued_endpoints:3,n_unique_country_endpoint_rows:424,
  n_verified_future_2027_outcomes:0,n_original_geo_transition_alerts_subset:15,
  n_original_geo_shadow_comparator_countries:196,
  observational_skill_demonstrated:false,
  independent_country_endpoints_or_country_years:false,
  first_commit_times_are_public_metadata_not_independent_notarization:true,
  cohorts,rows
 };
}

test("424 original country-variable rows, 196 distinct countries, 15 GEO subset only",()=>{
 const d=validateProspectiveRegistry(fakeDoc());
 assert.equal(d.rows.length,424);
 assert.equal(new Set(d.rows.map(r=>r.country_id)).size,196);
 assert.equal(d.rows.filter(r=>r.geo_transition_alert).length,15);
 assert.equal(d.n_verified_future_2027_outcomes,0);
});
test("filter by exact variable, partial accent-insensitive country, pagination",()=>{
 const d=fakeDoc();
 const filtered=filterProspectiveRegistry(d,{cohort:"ACD2027",query:"haiti",page:0});
 assert.equal(filtered.total,0); // ACD cohort's fixture only uses country IDs 1–32.
 const byGeo=filterProspectiveRegistry(d,{cohort:"GEO2027",query:"haiti"});
 assert.equal(byGeo.total,1);
 assert.equal(byGeo.rows[0].country,"Haití");
 const all=filterProspectiveRegistry(d,{page:19,pageSize:20});
 assert.equal(all.total,424);
 assert.equal(all.pageCount,22);
 assert.equal(all.rows.length,20);
 assert.equal(filterProspectiveRegistry(d,{page:22}).rows.length,4);
 assert.equal(filterProspectiveRegistry(d,{cohort:"ACD2027"}).total,32);
 assert.throws(()=>filterProspectiveRegistry(d,{cohort:"GEO2030"}));
 assert.throws(()=>filterProspectiveRegistry(d,{page:-1}));
});
test("render shows real source and pending flags, never invented official successes",()=>{
 const html=renderProspectiveRegistry(fakeDoc(),{cohort:"GEO2027",query:"haiti"});
 assert.match(html,/Haití/);
 assert.match(html,/42\s?%/);
 assert.match(html,/Sin resultado 2027/);
 assert.match(html,/2026-11-10/);
 assert.match(html,/github\.com\/idealab2026\/psicohistoria\/commit\//);
 assert.match(html,/ucdp\.uu\.se/);
 assert.match(html,/Alertas GEO incluidas/);
 assert.match(html,/2027/);
 assert.doesNotMatch(html,/Aciertos verificados: [1-9]/);
});
test("source-induced XSS is escaped in readable search result",()=>{
 const d=fakeDoc();
 d.rows[0].country="<img onerror=alert(1)>";
 const html=renderProspectiveRegistry(d,{cohort:"GEO2027"});
 assert.doesNotMatch(html,/<img onerror/);
 assert.match(html,/&lt;img onerror/);
});
test("tampered issue, extra cohort, outcome, alert or comparator fails closed",()=>{
 for(const mutate of [
   d=>d.cohorts.GEO2027.forecast_sha256="0".repeat(64),
   d=>d.cohorts.ACD2027.issue_utc="2027-01-01T00:00:00Z",
   d=>d.n_verified_future_2027_outcomes=1,
   d=>d.rows[0].observed_2027=1,
   d=>d.rows[0].certified_result=true,
   d=>d.rows.push({...d.rows[0]}),
   d=>d.rows[0].geo_transition_alert=null,
   d=>d.rows[0].p_primary=NaN,
   d=>d.rows[0].p_secondary.p_shadow_exploratorio=2,
   d=>d.rows[0].country_id=3000,
   d=>d.cohorts.ACD2027.source_url="https://bad.example.net/fake",
   d=>d.cohorts.NEWCONF2027.primary_model="p_shadow",
 ]){
  const d=fakeDoc();
  mutate(d);
  assert.throws(()=>validateProspectiveRegistry(d));
 }
});
