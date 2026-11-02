import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {buildScientificNetwork,createResearchFrameLoop} from "../src/neural.mjs";
import {renderVerifiedGeometry} from "../src/markov-svg.mjs";
import {scientificNeuralPanel,syntheticFourStateModel,scientificMarkovPanel,PUBLIC_CALENDAR_ORIGINS,PUBLIC_TREE_QUESTIONS,syntheticTreeQuestion,TRANSITIONS} from "../src/lab-renderers.mjs";
const demo=JSON.parse(readFileSync(new URL("../data/demo.json",import.meta.url),"utf8"));
test("Research network geometry has two lobes and all four conceptual tracks",()=>{
 const g=buildScientificNetwork(16);
 assert.equal(g.nodes.length,32);
 assert.ok(g.edges.length>32);
 assert.deepEqual(new Set(g.nodes.map(x=>x.track)),new Set([0,1,2,3]));
 const html=scientificNeuralPanel(demo.programs,"P1");
 assert.equal((html.match(/class="neural-orb"/g)||[]).length,4);
 assert.match(html,/data-science-neural/);
 assert.match(html,/data-motion-toggle/);
 assert.doesNotMatch(html,/private account|private endpoint|cloudflare/i);
});
test("Scientific animation loop has bounded lifecycle and respects dispose",()=>{
 let current=null,canceled=0,draws=0;
 const loop=createResearchFrameLoop({request:cb=>(current=cb,1),cancel:()=>{canceled++},draw:()=>{draws++}});
 loop.setEnabled(true);
 assert.ok(current);
 current(40);
 loop.setEnabled(false);
 loop.dispose();
 assert.ok(canceled>=1);
 assert.ok(draws>=0);
});
test("Synthetic Markov transitions are stochastic and obey 00/01/10/11 paths",()=>{
 for(const row of TRANSITIONS)assert.ok(Math.abs(row.reduce((a,b)=>a+b,0)-1)<1e-12);
 assert.deepEqual(TRANSITIONS.map(r=>r.map((v,i)=>v>0?i:null).filter(x=>x!==null)),[[0,1],[2,3],[0,1],[2,3]]);
 const d=syntheticFourStateModel();
 assert.equal(d.levels.length,8);
 assert.equal(d.snapshots.length,6);
 for(let t=1;t<d.levels.length;t++){
  const l=d.levels[t];
  assert.ok(Math.abs(l.distribution.reduce((a,b)=>a+b,0)-1)<1e-12);
  assert.ok(Math.abs(l.flows.reduce((a,b)=>a+b.mass,0)-1)<1e-12);
  for(const e of l.flows)assert.ok(e.mass>=0 && TRANSITIONS[e.from][e.to]>0);
 }
 assert.equal(d.observedStates.length,0);
 assert.deepEqual(d.country,{name:"Ejemplo sintético"});
});
test("Scientific SVG renderer displays the complete eight-column time tree and scientific interactions",()=>{
 const d=syntheticFourStateModel();
 const svg=renderVerifiedGeometry(d,4,null,false,true);
 assert.match(svg,/class="future-graph"/);
 assert.match(svg,/data-fnode="7:3"/);
 assert.match(svg,/data-fedge="7:/);
 assert.match(svg,/future-core-glow/);
 assert.match(svg,/>2025<\/text>/);
 assert.match(svg,/>2018<\/text>/);
 assert.match(svg,/>2019<\/text>/);
 assert.doesNotMatch(svg,/future-observed-halo|REAL · FINAL/);
 const selected=renderVerifiedGeometry(d,4,{kind:"node",level:3,state:1},false,true);
 assert.match(selected,/class="future-node selected"/);
 const html=scientificMarkovPanel({horizon:3});
 assert.equal((html.match(/data-action="markov-year"/g)||[]).length,6);
 assert.equal((html.match(/data-action="markov-origin"/g)||[]).length,2);
 assert.match(html,/>2018<\/strong>/);
 assert.match(html,/>2019<\/strong>/);
 assert.match(html,/>2025<\/strong>/);
 assert.match(html,/NINGÚN PAÍS REAL/);
 assert.throws(()=>syntheticFourStateModel(22));
 assert.throws(()=>scientificMarkovPanel({horizon:7}));
});
test("Public release uses the source-based canvas, not the substitute orbit/tree diagrams",()=>{
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(site,/scientificNeuralPanel\(d\.programs,state\.program\)/);
 assert.match(site,/enableScientificNeural/);
 assert.match(site,/scientificMarkovPanel/);
 assert.doesNotMatch(site,/scenarioBranches\(d\.branches/);
 assert.doesNotMatch(site,/stateTransitionDiagram\(state\.flowState/);
 const index=readFileSync(new URL("../index.html",import.meta.url),"utf8");
 assert.match(index,/src\/site\.mjs/);
});


test("Every scientific-tree column has a real calendar year, including full 2016–2025 and 2020–2025 ranges",()=>{
 assert.deepEqual(PUBLIC_CALENDAR_ORIGINS,[2016,2020]);
 for(const [origin,cutoff,span] of [[2016,2014,10],[2020,2018,6]]){
  const model=syntheticFourStateModel(span,origin);
  assert.equal(model.cutoff,cutoff);
  assert.equal(model.origin,origin);
  assert.equal(model.levels.length,span+2);
  assert.deepEqual(model.levels.map(x=>x.year),
   Array.from({length:span+2},(_,i)=>cutoff+i));
  assert.deepEqual(model.snapshots.map(x=>x.endYear),
   Array.from({length:span},(_,i)=>origin+i));
  const html=scientificMarkovPanel({horizon:span,origin});
  const svg=renderVerifiedGeometry(model,span,null,false,true);
  for(let year=cutoff;year<=2025;year++){
   assert.match(svg,new RegExp('class="future-year"[^>]*>'+year+'<\\/text>'));
   assert.match(html,new RegExp('>'+year+'<strong>|>'+year+'<\\/strong>|>'+year+'<\\/text>'));
  }
  assert.equal((html.match(/data-action="markov-year"/g)||[]).length,span);
  assert.match(html,/MALLA SINTÉTICA/);
  assert.match(html,/probabilidades y resultados totalmente ficticios/);
  assert.doesNotMatch(html,/github\.com|ORIGEN_HISTORICO/);
  assert.doesNotMatch(svg,/T\+\d|T0/);
  assert.equal(model.observedStates.length,0);
 }
 assert.throws(()=>syntheticFourStateModel(7,2020),/INVALID_HORIZON/);
 assert.throws(()=>syntheticFourStateModel(2,2027),/INVALID_ILLUSTRATIVE_ORIGIN/);
});
test("The public explorer binds origin selection, annual focus, and complete-year responsive layout",()=>{
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 const css=readFileSync(new URL("../styles.css",import.meta.url),"utf8");
 assert.match(site,/markovOrigin:2020/);
 assert.match(site,/case "markov-origin"/);
 assert.match(site,/2026-state.markovOrigin/);
 assert.match(site,/chart\.scrollLeft/);
 assert.match(css,/\.markov-origin-controls/);
 assert.match(css,/\.science-markov-panel \.future-year/);
 assert.match(css,/\.future-graph-scroll\{[^}]*overflow-x:auto/);
});


test("Six questions are compatible with ONE unchanged synthetic distribution, without retraining",()=>{
 const model=syntheticFourStateModel(6,2020),h=6;
 assert.deepEqual(PUBLIC_TREE_QUESTIONS.map(x=>x.id),
  ["atleast25","below25","entry","exit","persistence","stable_low"]);
 const values=Object.fromEntries(PUBLIC_TREE_QUESTIONS.map(q=>[q.id,syntheticTreeQuestion(model,h,q.id)]));
 const masses=model.snapshots[h-1].distribution;
 const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-12);
 close(values.atleast25.yes,masses[1]+masses[3]);
 close(values.below25.yes,masses[0]+masses[2]);
 close(values.entry.yes,masses[1]);
 close(values.exit.yes,masses[2]);
 close(values.persistence.yes,masses[3]);
 close(values.stable_low.yes,masses[0]);
 close(values.atleast25.yes+values.below25.yes,1);
 for(const value of Object.values(values)){
  close(value.yes+value.no,1);
  assert.equal(value.year,2025);
 }
 const html=scientificMarkovPanel({horizon:h,origin:2020,question:"persistence"});
 assert.equal((html.match(/<option value="(?:atleast25|below25|entry|exit|persistence|stable_low)"/g)||[]).length,6);
 assert.match(html,/data-public-question/);
 assert.match(html,/option value="persistence" selected/);
 assert.match(html,/data-science-markov/);
 assert.match(html,/class="science-tree-state matches-question"/);
 assert.match(html,/Porcentajes exclusivamente sintéticos/);
 assert.doesNotMatch(html,/predicción certificada|datos científicos reales/i);
 assert.throws(()=>syntheticTreeQuestion(model,3,"war"),/INVALID_ILLUSTRATIVE_QUESTION/);
 assert.throws(()=>syntheticTreeQuestion(model,7,"atleast25"),/INVALID_ILLUSTRATIVE_QUESTION/);
});
test("Public web interaction changes question without altering the selected origin, year or probabilities",()=>{
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(site,/markovQuestion:"atleast25"/);
 assert.match(site,/case "markov-origin"/);
 assert.match(site,/data-public-question/);
 assert.match(site,/state\.markovQuestion=select\.value/);
 assert.match(site,/scrollLeft=scroll/);
 const css=readFileSync(new URL("../styles.css",import.meta.url),"utf8");
 assert.match(css,/\.science-tree-state\.matches-question/);
 assert.match(css,/\.science-prediction-question/);
});
