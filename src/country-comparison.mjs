// A read-only, client-side comparison of country-specific historical Markov catalogues.
// No network I/O, private data export, forecasting issuance or observed-outcome scoring.
export const COUNTRY_MODELS=Object.freeze([
 {id:"country_shrinkage",label:"Markov por país regularizado"},
 {id:"markov",label:"Markov global"},
 {id:"frequency",label:"Frecuencia constante"},
 {id:"persistence",label:"Persistencia"},
 {id:"memory2",label:"Memoria de dos estados"}
]);
export const FOUR_STATES=Object.freeze([
 "00 · Bajo → bajo","01 · Entrada ≥25","10 · Salida <25","11 · Persistencia ≥25"
]);
const isObj=x=>x!==null&&typeof x==="object"&&!Array.isArray(x);
const nonNegativeInt=x=>Number.isSafeInteger(x)&&x>=0;
const row=x=>Array.isArray(x)&&x.length===2&&x.every(nonNegativeInt);
const rows=(x,n)=>Array.isArray(x)&&x.length===n&&x.every(row);
const sha=s=>typeof s==="string"&&/^[a-f0-9]{64}$/i.test(s);
const sum=a=>a.reduce((x,y)=>x+y,0);
const PROTOCOL="psychohistory.futures.catalog.v1";
const VINTAGE="UCDP OrganizedViolenceCY 26.1";
export function validateCountryCatalog(d){
 const expected=d?.origin===2016?{n:195,h:10}:d?.origin===2020?{n:196,h:6}:null;
 if(!expected||d.schema!==PROTOCOL||d.version!=="ucdp-futures-v1"||
   d.runType!=="retrospective_revised_release"||d.vintageVerified!==false||
   d.prospectiveEligible!==false||d.datasetVersion!==VINTAGE||
   !sha(d.runId)||!sha(d.protocolSha256)||!sha(d.codeSha256)||
   d.cutoff!==d.origin-2||d.observedThrough!==2025||
   d.maxHorizon!==expected.h||d.priorStrength!==20||
   !rows(d.global?.transitions,2)||!rows(d.global?.memory,4)||
   !row(d.global?.frequency)||sum(d.global.frequency)===0||
   !Array.isArray(d.countries)||d.countries.length!==expected.n)
   throw Error("CATALOGO_HISTORICO_NO_VALIDADO");
 const ids=new Set();
 for(const c of d.countries){
   if(!nonNegativeInt(c.id)||ids.has(c.id)||typeof c.name!=="string"||
      !c.name.trim()||c.name.length>120||!nonNegativeInt(c.initial)||c.initial>3||
      !rows(c.counts,2))throw Error("PAIS_HISTORICO_INVALIDO");
   ids.add(c.id);
 }
 return d;
}
function decodeCandidate(value){
 if(isObj(value)&&value.schema===PROTOCOL)return value;
 if(typeof value!=="string"||value.length<100||value.length>350000||!value.includes(PROTOCOL))return null;
 // Parse only a bounded exact JSON value, not arbitrary text or embedded content.
 if(!value.trimStart().startsWith("{"))return null;
 try{const d=JSON.parse(value);return isObj(d)&&d.schema===PROTOCOL?d:null;}catch{return null;}
}
export function discoverHistoricalCountryCatalogs(root){
 if(!root||typeof root!=="object")throw Error("ARCHIVO_JSON_REQUERIDO");
 const queue=[root],found=new Map();let examined=0;
 // Accept either institutional 'futuresCatalogs' JSON or the original
 // experiment notes embedded within the 11-table scientific workbook.
 while(queue.length&&examined<100000&&found.size<2){
   const value=queue.pop();examined++;
   const candidate=decodeCandidate(value);
   if(candidate){
     const validated=validateCountryCatalog(candidate);
     const old=found.get(validated.origin);
     if(old&&old.runId!==validated.runId)throw Error("CATALOGOS_INCOMPATIBLES");
     found.set(validated.origin,validated);
     continue;
   }
   if(Array.isArray(value)){
     for(let i=value.length-1;i>=0;i--)queue.push(value[i]);
   } else if(isObj(value)){
     for(const [,v] of Object.entries(value))if(v!==null&&(typeof v==="object"||
       (typeof v==="string"&&v.includes(PROTOCOL))))queue.push(v);
   }
 }
 return [...found.values()].sort((a,b)=>a.origin-b.origin);
}
function rates(catalog,c,model){
 if(!COUNTRY_MODELS.some(x=>x.id===model))throw Error("MODELO_NO_ADMITIDO");
 return [0,1,2,3].map(state=>{
   const previous=state%2;
   if(model==="persistence")return previous;
   if(model==="country_shrinkage"){
     const local=c.counts[previous],glob=catalog.global.transitions[previous];
     const globalRate=(glob[1]+1)/(sum(glob)+2);
     return (local[1]+catalog.priorStrength*globalRate)/(sum(local)+catalog.priorStrength);
   }
   const counts=model==="frequency"?catalog.global.frequency:
     model==="markov"?catalog.global.transitions[previous]:catalog.global.memory[state];
   return (counts[1]+1)/(sum(counts)+2);
 });
}
export function historicalCountryTrajectory(catalog,countryId,model="country_shrinkage"){
 validateCountryCatalog(catalog);
 const country=catalog.countries.find(x=>String(x.id)===String(countryId));
 if(!country)throw Error("PAIS_NO_ENCONTRADO");
 const matrixRates=rates(catalog,country,model);
 const levels=[{year:catalog.cutoff,distribution:[0,1,2,3].map(i=>Number(i===country.initial)),flows:[]}];
 let dist=[...levels[0].distribution];
 for(let step=1;step<=catalog.maxHorizon+1;step++){
   const next=[0,0,0,0],flows=[];
   dist.forEach((mass,from)=>{
     const low=2*(from%2),p=matrixRates[from];
     for(const [to,conditional] of [[low,1-p],[low+1,p]]){
       const flow=mass*conditional;
       next[to]+=flow;
       if(conditional>0&&flow>0)flows.push({from,to,conditional,mass:flow});
     }
   });
   if(next.some(p=>!Number.isFinite(p)||p<0||p>1+1e-9)||
      Math.abs(sum(next)-1)>1e-9)throw Error("MASA_PROBABILISTICA_INVALIDA");
   dist=next;
   levels.push({year:catalog.cutoff+step,distribution:[...next],flows});
 }
 return {
   country:{id:country.id,name:country.name},initial:country.initial,
   model,origin:catalog.origin,cutoff:catalog.cutoff,maxHorizon:catalog.maxHorizon,
   historicalRevision:true,vintageVerified:false,prospectiveEligible:false,
   observedStates:[],
   snapshots:levels.slice(2).map(l=>({endYear:l.year,distribution:[...l.distribution],paths:[]})),
   levels:levels.map((l,i)=>({...l,kind:i===0?"corte":i===1?"puente_no_observado":"proyeccion_retroactiva",
     probabilityAtLeast25:l.distribution[1]+l.distribution[3]}))
 };
}
export function compareHistoricalCountries(catalog,countryIds,model="country_shrinkage",question="atleast25"){
 if(!Array.isArray(countryIds)||countryIds.length<1||countryIds.length>6||
    new Set(countryIds.map(String)).size!==countryIds.length)throw Error("ESCOGE_ENTRE_UNO_Y_SEIS_PAISES");
 if(!["atleast25","entry","exit","persistence","below25"].includes(question))throw Error("PREGUNTA_NO_ADMITIDA");
 const states={atleast25:[1,3],entry:[1],exit:[2],persistence:[3],below25:[0,2]}[question];
 const series=countryIds.map(id=>{
   const t=historicalCountryTrajectory(catalog,id,model);
   return {...t,points:t.levels.filter(l=>l.year>=catalog.origin).map(l=>({
     year:l.year,probability:states.reduce((n,s)=>n+l.distribution[s],0),
     distribution:l.distribution
   }))};
 });
 return {origin:catalog.origin,cutoff:catalog.cutoff,model,question,
   years:series[0].points.map(p=>p.year),series,
   label:"RETROSPECTIVO · revisión 26.1 · disponibilidad histórica no acreditada"};
}
