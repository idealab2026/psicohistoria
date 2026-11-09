import test from "node:test";
import assert from "node:assert/strict";
import {validateCountryCatalog,discoverHistoricalCountryCatalogs,historicalCountryTrajectory,
 compareHistoricalCountries,COUNTRY_MODELS} from "../src/country-comparison.mjs";
const hex="a".repeat(64);
function example(origin=2020){
 const n=origin===2020?196:195;
 return {schema:"psychohistory.futures.catalog.v1",version:"ucdp-futures-v1",
   runType:"retrospective_revised_release",vintageVerified:false,prospectiveEligible:false,
   datasetVersion:"UCDP OrganizedViolenceCY 26.1",
   runId:hex,protocolSha256:"b".repeat(64),codeSha256:"c".repeat(64),
   origin,cutoff:origin-2,observedThrough:2025,maxHorizon:2026-origin,priorStrength:20,
   global:{frequency:[13,8],transitions:[[7,3],[2,8]],memory:[[9,1],[5,4],[1,8],[2,10]]},
   countries:Array.from({length:n},(_,i)=>({id:1000+i,name:"País "+i,
      initial:i%4,counts:[[10+i%7,1+(i%5)],[4+(i%3),10+(i%11)]],
      observedStates:Array.from({length:2028-origin},()=>null)}))
 };
}
test("admits only complete retrospective original 2016/2020 catalogues",()=>{
 assert.equal(validateCountryCatalog(example(2016)).countries.length,195);
 assert.equal(validateCountryCatalog(example(2020)).countries.length,196);
 assert.throws(()=>validateCountryCatalog({...example(),vintageVerified:true}),/CATALOGO_HISTORICO_NO_VALIDADO/);
 assert.throws(()=>validateCountryCatalog({...example(),countries:example().countries.slice(1)}),/CATALOGO_HISTORICO_NO_VALIDADO/);
 assert.throws(()=>validateCountryCatalog({...example(),prospectiveEligible:true}),/CATALOGO_HISTORICO_NO_VALIDADO/);
});
test("can discover both historic catalogues from canonical payload or private cell notes",()=>{
 const twenty=example(2020),sixteen=example(2016);
 assert.deepEqual(discoverHistoricalCountryCatalogs({futuresCatalogs:[sixteen,twenty]}).map(x=>x.origin),[2016,2020]);
 const archive={tables:[{kind:"experiments",dataRows:[{cells:[{lexicalValue:JSON.stringify(twenty)},{lexicalValue:JSON.stringify(sixteen)}]}]}]};
 assert.deepEqual(discoverHistoricalCountryCatalogs(archive).map(x=>x.origin),[2016,2020]);
 assert.deepEqual(discoverHistoricalCountryCatalogs({other:{notes:"not a catalog"}}),[]);
});
test("per-country transition matrix, probability mass, and visible years remain sound",()=>{
 const cat=example(2020);
 const t=historicalCountryTrajectory(cat,1000,"country_shrinkage");
 assert.equal(t.levels.length,8);
 assert.equal(t.levels[0].year,2018);
 assert.equal(t.levels[1].kind,"puente_no_observado");
 assert.equal(t.levels[2].year,2020);
 assert.equal(t.levels.at(-1).year,2025);
 assert.equal(t.vintageVerified,false);
 assert.equal(t.prospectiveEligible,false);
 for(const level of t.levels){
  assert.ok(Math.abs(level.distribution.reduce((a,b)=>a+b,0)-1)<1e-10);
  assert.ok(level.probabilityAtLeast25>=0&&level.probabilityAtLeast25<=1);
 }
 assert.equal(historicalCountryTrajectory(cat,1000,"persistence").levels.at(-1).probabilityAtLeast25,0);
 assert.equal(historicalCountryTrajectory(cat,1001,"persistence").levels.at(-1).probabilityAtLeast25,1);
});
test("country-specific lines differ without mixing origins or using future outcomes",()=>{
 const cat=example(2020),copy=JSON.stringify(cat);
 const out=compareHistoricalCountries(cat,[1000,1004],"country_shrinkage","atleast25");
 assert.deepEqual(out.years,[2020,2021,2022,2023,2024,2025]);
 assert.notDeepEqual(out.series[0].points.map(p=>p.probability),
   out.series[1].points.map(p=>p.probability));
 const global=compareHistoricalCountries(cat,[1000,1004],"markov","atleast25");
 assert.deepEqual(global.series[0].points.map(p=>p.probability),
   global.series[1].points.map(p=>p.probability));
 assert.equal(JSON.stringify(cat),copy);
 assert.throws(()=>compareHistoricalCountries(cat,[1000,1000]),/ESCOGE_ENTRE_UNO_Y_SEIS/);
 assert.throws(()=>compareHistoricalCountries(cat,[1000],"markov","fake"),/PREGUNTA_NO_ADMITIDA/);
 assert.equal(COUNTRY_MODELS.length,5);
});
