// Publicly reproducible retrospective country-year Markov trees (UCDP CC BY 4.0).
// No private archive, user file uploads, personal repositories, or emissions.
import {COUNTRY_MODELS,FOUR_STATES,validateCountryCatalog,historicalCountryTrajectory} from "./country-comparison.mjs";
import {renderVerifiedGeometry} from "./markov-svg.mjs";
const catalogues=new Map();
let sourceNote="";
const esc=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct=x=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(x);
const QUESTIONS=[
 ["atleast25","25 o más muertes",[1,3]],["below25","Menos de 25 muertes",[0,2]],
 ["entry","Entrada al episodio",[1]],["exit","Salida del episodio",[2]],
 ["persistence","Persistencia del episodio",[3]],["stable_low","Permanecer bajo el umbral",[0]]
];
export function getHistoricalCatalog(origin){return catalogues.get(Number(origin))||null;}
export function setCountrySourceError(message){sourceNote=String(message||"Fuente oficial temporalmente no disponible").slice(0,180);}
export function acceptPublicCountryCatalogs(input){
 if(input?.schema!=="idealab.psico.public_official_country_markov.v1"||
   input.forecastsIssued!==0||input.prospectiveSkillVerified!==false||
   input.source?.dataset!=="UCDP OrganizedViolenceCY 26.1"||
   input.source?.license!=="CC BY 4.0"||input.source?.rowCount!==7132||
   !/^[0-9a-f]{64}$/i.test(input.source?.sha256||"")||
   !Array.isArray(input.catalogs)||input.catalogs.length!==2)
   throw Error("CATALOGO_PUBLICO_NO_ACREDITADO");
 const tmp=new Map();
 for(const c of input.catalogs){
   if(c.sourceClass!=="PUBLIC_OFFICIAL_INDEPENDENT_RECONSTRUCTION"||
     c.sourceSha256!==input.source.sha256||
     (c.origin!==2016&&c.origin!==2020)||tmp.has(c.origin))
     throw Error("COHORTE_PUBLICA_INCONSISTENTE");
   validateCountryCatalog(c);tmp.set(c.origin,c);
 }
 if(tmp.size!==2||![2016,2020].every(y=>tmp.has(y)))
   throw Error("ORIGENES_INCOMPLETOS");
 for(const [id,c] of tmp)catalogues.set(id,c);
 sourceNote="";
 return [...tmp.values()].map(c=>({origin:c.origin,countries:c.countries.length}));
}
export function renderHistoricalTree(state){
 const c=catalogues.get(Number(state.countryTreeOrigin))||catalogues.get(2020)||catalogues.get(2016);
 if(!c){
   return '<section class="panel historical-country-tree" aria-label="Árbol de predicciones por país">'+
     '<div class="eyebrow">PREDICCIONES · ÁRBOL POR PAÍS</div><h3>País y pregunta</h3>'+
     '<p class="notice info" role="status">'+esc(sourceNote||"Cargando países y modelos oficiales…")+'</p>'+
     '<p class="viz-foot">Fuente: UCDP 26.1 · datos retrospectivos. No se muestran probabilidades inventadas si falta la fuente.</p></section>';
 }
 const country=c.countries.find(x=>String(x.id)===String(state.countryTreeId))||
    c.countries.find(x=>x.name.toLowerCase().includes("spain"))||
    [...c.countries].sort((a,b)=>a.name.localeCompare(b.name,"es"))[0];
 const model=COUNTRY_MODELS.some(x=>x.id===state.countryTreeModel)?state.countryTreeModel:"country_shrinkage";
 const answer=QUESTIONS.find(x=>x[0]===state.countryTreeQuestion)||QUESTIONS[0];
 const timeline=historicalCountryTrajectory(c,country.id,model);
 const year=Number.isSafeInteger(state.countryTreeYear)&&state.countryTreeYear>=c.origin&&state.countryTreeYear<=2025?
   state.countryTreeYear:2025;
 const masses=timeline.levels[year-c.cutoff].distribution;
 const p=answer[2].reduce((v,s)=>v+masses[s],0);
 const options=(items,choice)=>items.map(([id,label])=>'<option value="'+esc(id)+'"'+
   (String(id)===String(choice)?' selected':'')+'>'+esc(label)+'</option>').join("");
 const names=[...c.countries].sort((a,b)=>a.name.localeCompare(b.name,"es")).map(x=>[x.id,x.name]);
 const models=COUNTRY_MODELS.map(x=>[x.id,x.label]);
 const origins=[...catalogues.values()].sort((a,b)=>a.origin-b.origin).map(x=>[x.origin,"Árbol "+x.origin]);
 const years=Array.from({length:c.maxHorizon},(_,i)=>[c.origin+i,String(c.origin+i)]);
 const controls='<div class="historic-country-controls">'+
  '<label>Sociedad<select id="tree-country-select" aria-label="Selecciona el país">'+options(names,country.id)+'</select></label>'+
  '<label>¿Qué quieres calcular?<select id="tree-country-question">'+options(QUESTIONS.map(q=>[q[0],q[1]]),answer[0])+'</select></label>'+
  '<label>Árbol<select id="tree-country-origin">'+options(origins,c.origin)+'</select></label>'+
  '<label>Modelo<select id="tree-country-model">'+options(models,model)+'</select></label>'+
  '<label>Año<select id="tree-country-year">'+options(years,year)+'</select></label>'+
  '</div>';
 const graph=renderVerifiedGeometry(timeline,year-c.origin+1,state.countryTreeSelection,false,true);
 const states=FOUR_STATES.map((name,i)=>'<div class="historic-state'+(answer[2].includes(i)?' selected':'')+
  '"><strong>'+esc(name)+'</strong><span>'+pct(masses[i])+'</span></div>').join("");
 return '<section class="panel historical-country-tree" data-country-tree aria-label="Árbol de predicciones por país">'+
  '<div class="viz-heading"><div><div class="eyebrow">PREDICCIONES · ESTUDIO HISTÓRICO</div>'+
  '<h3>'+esc(country.name)+' · '+c.origin+'–2025</h3></div>'+
  '<span class="viz-label">RETROSPECTIVO · UCDP 26.1</span></div>'+
  controls+
  '<div class="historic-tree-summary"><div><small>SÍ · '+year+'</small><strong>'+pct(p)+'</strong></div>'+
  '<div><small>NO · '+year+'</small><strong>'+pct(1-p)+'</strong></div></div>'+
  '<div class="future-graph-scroll" data-real-markov tabindex="0" role="region" aria-label="Árbol de '+esc(country.name)+' desde '+c.cutoff+' hasta 2025">'+graph+'</div>'+
  '<div class="historic-state-grid">'+states+'</div>'+
  '<p class="viz-foot">Fuente: <a href="https://ucdp.uu.se/downloads/" target="_blank" rel="noopener noreferrer">UCDP OrganizedViolenceCY 26.1</a> (CC BY 4.0). Reconstrucción independiente con edición revisada en 2026; <strong>no equivale a una predicción registrada en '+c.origin+'</strong> ni demuestra aciertos prospectivos. 00/01/10/11 describen la transición anual respecto al umbral de 25 muertes de violencia estatal.</p>'+
  '</section>';
}
