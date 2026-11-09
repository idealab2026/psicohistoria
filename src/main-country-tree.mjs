// Original four-state historical trees rendered entirely in this browser.
// These catalogs are supplied via File API and never leave local memory.
import {COUNTRY_MODELS,FOUR_STATES,discoverHistoricalCountryCatalogs,historicalCountryTrajectory} from "./country-comparison.mjs";
import {renderVerifiedGeometry} from "./markov-svg.mjs";
const catalogs=new Map();
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct=x=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(x);
const QUESTIONS=[
 ["atleast25","25 o más muertes",[1,3]],
 ["below25","Menos de 25 muertes",[0,2]],
 ["entry","Entrada al episodio",[1]],
 ["exit","Salida del episodio",[2]],
 ["persistence","Persistencia del episodio",[3]],
 ["stable_low","Permanece por debajo",[0]]
];
export function getHistoricalCatalog(origin){return catalogs.get(Number(origin))||null;}
export function acceptHistoricalFile(json){
 const found=discoverHistoricalCountryCatalogs(json);
 if(!found.length)throw Error("NO_SE_ENCONTRARON_CATALOGOS_MARKOV_2016_2020");
 for(const item of found){
   const old=catalogs.get(item.origin);
   if(old&&old.runId!==item.runId)throw Error("CONFLICTO_DE_CATALOGOS_EN_MEMORIA");
 }
 for(const item of found)catalogs.set(item.origin,item);
 return found.map(c=>({origin:c.origin,countries:c.countries.length}));
}
export function renderHistoricalTree(state){
 let chosen=getHistoricalCatalog(state.countryTreeOrigin);
 if(!chosen)chosen=catalogs.get(2020)||catalogs.get(2016)||null;
 const source='<div class="tree-source-bar"><label for="tree-private-file">Catálogo histórico privado (.json)'+
  '<input type="file" id="tree-private-file" accept=".json,application/json" aria-label="Cargar archivo histórico privado para seleccionar países"></label>'+
  '<p>Se procesa únicamente en la memoria de tu navegador. Ningún dato se envía al servidor.</p></div>';
 if(!chosen){
   return '<section class="panel historical-country-tree" aria-label="Árbol predictivo real por país">'+
    '<div class="eyebrow">ÁRBOLES HISTÓRICOS · PAÍSES</div><h3>Seleccionar país y modelo</h3>'+
    '<p>El árbol público anterior era una simulación sin países. Para explorar España, Túnez o cualquier otro país con las probabilidades del estudio, abre aquí el catálogo original de IDEA LAB.</p>'+
    source+'<p role="status" data-country-file-status class="notice info">Sin catálogo privado cargado · Orígenes 2016 y 2020 compatibles · 195/196 países.</p>'+
    '<p><a href="./trabajo.html">Abrir cuaderno completo y comparar varios países</a></p></section>';
 }
 const ids=new Set(chosen.countries.map(c=>String(c.id)));
 const country=chosen.countries.find(c=>String(c.id)===String(state.countryTreeId))||
   [...chosen.countries].sort((a,b)=>a.name.localeCompare(b.name,"es"))[0];
 const model=COUNTRY_MODELS.some(x=>x.id===state.countryTreeModel)?state.countryTreeModel:"country_shrinkage";
 const data=historicalCountryTrajectory(chosen,country.id,model);
 const max=chosen.origin+chosen.maxHorizon-1;
 const year=Number.isInteger(state.countryTreeYear)&&state.countryTreeYear>=chosen.origin&&state.countryTreeYear<=max?
   state.countryTreeYear:max;
 const question=QUESTIONS.find(x=>x[0]===state.countryTreeQuestion)||QUESTIONS[0];
 const distribution=data.levels[year-chosen.cutoff].distribution;
 const yes=question[2].reduce((a,i)=>a+distribution[i],0);
 const originOptions=[...catalogs.values()].sort((a,b)=>a.origin-b.origin).map(c=>
   '<option value="'+c.origin+'"'+(c.origin===chosen.origin?' selected':'')+'>Origen '+c.origin+' · '+c.countries.length+' países</option>').join("");
 const countryOptions=[...chosen.countries].sort((a,b)=>a.name.localeCompare(b.name,"es")).map(c=>
   '<option value="'+c.id+'"'+(c.id===country.id?' selected':'')+'>'+esc(c.name)+'</option>').join("");
 const modelOptions=COUNTRY_MODELS.map(x=>'<option value="'+x.id+'"'+(x.id===model?' selected':'')+'>'+esc(x.label)+'</option>').join("");
 const questionOptions=QUESTIONS.map(x=>'<option value="'+x[0]+'"'+(x[0]===question[0]?' selected':'')+'>'+esc(x[1])+'</option>').join("");
 const yearOptions=Array.from({length:chosen.maxHorizon},(_,i)=>chosen.origin+i).map(y=>
   '<option value="'+y+'"'+(y===year?' selected':'')+'>'+y+'</option>').join("");
 const graph=renderVerifiedGeometry(data,year-chosen.origin+1,state.countryTreeSelection,false,true);
 const states=FOUR_STATES.map((name,i)=>'<div class="historic-state'+(question[2].includes(i)?' selected':'')+'"><strong>'+esc(name)+'</strong><span>'+pct(distribution[i])+'</span></div>').join("");
 const label=chosen.datasetVersion+" · revisión retrospectiva; disponibilidad histórica de la edición NO verificada";
 return '<section class="panel historical-country-tree" aria-label="Árbol de probabilidades por país" data-country-tree>'+
  '<div class="eyebrow">ÁRBOL REAL · ANÁLISIS RETROSPECTIVO · '+esc(chosen.origin)+'</div>'+
  '<div class="viz-heading"><div><h3>'+esc(country.name)+' · árbol de cuatro estados</h3>'+
  '<p>'+esc(label)+'</p></div><span class="viz-label">NO ES UNA PREDICCIÓN EMITIDA</span></div>'+
  '<div class="historic-country-controls">'+
  '<label>Origen<select id="tree-country-origin">'+originOptions+'</select></label>'+
  '<label>País<select id="tree-country-select">'+countryOptions+'</select></label>'+
  '<label>Modelo<select id="tree-country-model">'+modelOptions+'</select></label>'+
  '<label>Fenómeno<select id="tree-country-question">'+questionOptions+'</select></label>'+
  '<label>Año<select id="tree-country-year">'+yearOptions+'</select></label></div>'+
  '<div class="historic-tree-summary"><div><small>SÍ · '+year+'</small><strong>'+pct(yes)+'</strong></div>'+
  '<div><small>NO · '+year+'</small><strong>'+pct(1-yes)+'</strong></div></div>'+
  '<div class="future-graph-scroll" tabindex="0" data-real-markov aria-label="Árbol de '+esc(country.name)+' desde '+chosen.cutoff+' hasta '+max+'">'+graph+'</div>'+
  '<div class="historic-state-grid">'+states+'</div>'+
  '<p class="viz-foot">2016/2020: ramas por país con transición regularizada, Markov global u otras referencias. Corte '+chosen.cutoff+', puente '+(chosen.origin-1)+' no observado en emisión, años '+chosen.origin+'–'+max+'. El resultado posterior nunca se usa para ajustar este árbol. Los datos privados no salen del navegador.</p>'+
  source+'<p role="status" data-country-file-status class="notice info">'+esc(country.name)+
  ' seleccionado de '+chosen.countries.length+' países.</p>'+
  '<p><a class="ghost" href="./trabajo.html">Comparar hasta seis países en líneas superpuestas</a></p></section>';
}
