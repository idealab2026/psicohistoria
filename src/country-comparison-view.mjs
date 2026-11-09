import {COUNTRY_MODELS,FOUR_STATES,discoverHistoricalCountryCatalogs,compareHistoricalCountries} from "./country-comparison.mjs";
const $=id=>document.getElementById(id);
const NS="http://www.w3.org/2000/svg";
const COLORS=["#5fd4e7","#f8ad6a","#c2a1ff","#a8de87","#ff8bb3","#e9d47b"];
const DASH=["","8 4","2 4","11 4 2 4","5 6","13 5"];
const pct=n=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:1}).format(n);
function el(tag,text,cls){
 const n=document.createElement(tag);
 if(text!==undefined)n.textContent=String(text);
 if(cls)n.className=cls;
 return n;
}
function svg(tag,attrs={},label){
 const n=document.createElementNS(NS,tag);
 for(const [key,value] of Object.entries(attrs))n.setAttribute(key,String(value));
 if(label!==undefined){const t=document.createElementNS(NS,"title");t.textContent=String(label);n.append(t);}
 return n;
}
const selection=new Map(),catalogs=new Map();
let chosenYear=null;
function current(){
 return catalogs.get(Number($("comparison-origin").value));
}
function ids(catalog){
 const key=catalog.origin;
 if(!selection.has(key)){
   const ordered=[...catalog.countries].sort((a,b)=>a.name.localeCompare(b.name,"es"));
   selection.set(key,new Set(ordered.slice(0,Math.min(3,ordered.length)).map(x=>x.id)));
 }
 return selection.get(key);
}
function renderList(){
 const catalog=current();if(!catalog)return;
 const picked=ids(catalog),root=$("comparison-countries"),query=$("comparison-country-search").value.trim().toLocaleLowerCase("es");
 root.replaceChildren();
 const countries=[...catalog.countries].sort((a,b)=>a.name.localeCompare(b.name,"es"));
 const filtered=countries.filter(c=>c.name.toLocaleLowerCase("es").includes(query));
 for(const c of filtered.slice(0,300)){
   const label=el("label");
   const input=document.createElement("input");input.type="checkbox";input.checked=picked.has(c.id);
   input.setAttribute("aria-label","Incluir "+c.name);
   input.addEventListener("change",()=>{
     if(input.checked){
       if(picked.size>=6){input.checked=false;$("comparison-source-status").textContent="Máximo seis países simultáneos.";return;}
       picked.add(c.id);
     }else if(picked.size===1){input.checked=true;$("comparison-source-status").textContent="Selecciona como mínimo un país.";return;}
     else picked.delete(c.id);
     renderResult();
   });
   label.append(input,el("span",c.name));root.append(label);
 }
 if(!filtered.length)root.append(el("p","No hay coincidencias."));
}
function drawChart(result){
 const root=$("comparison-chart");root.replaceChildren();
 const years=result.years;
 const l=75,r=1055,t=35,b=326;
 const x=y=>years.length===1?(l+r)/2:l+(y-years[0])*(r-l)/(years.at(-1)-years[0]);
 const y=p=>b-(p*(b-t));
 for(const tick of [0,.25,.5,.75,1]){
   root.append(svg("line",{x1:l,y1:y(tick),x2:r,y2:y(tick),stroke:"#365166","stroke-width":tick===0?1.4:.8,"stroke-dasharray":"3 7"}));
   const label=svg("text",{x:57,y:y(tick)+5,fill:"#a8c6d5","font-size":14,"text-anchor":"end"});label.textContent=Math.round(tick*100)+" %";root.append(label);
 }
 for(const year of years){
   const label=svg("text",{x:x(year),y:350,fill:"#b7ceda","font-size":13,"text-anchor":"middle"});label.textContent=year;root.append(label);
 }
 result.series.forEach((line,i)=>{
   const color=COLORS[i],dash=DASH[i],d=line.points.map((p,j)=>(j?"L":"M")+x(p.year).toFixed(2)+" "+y(p.probability).toFixed(2)).join(" ");
   const path=svg("path",{d,stroke:color,fill:"none","stroke-width":3.4,"stroke-dasharray":dash,"stroke-linecap":"round","stroke-linejoin":"round"},
     line.country.name+" · "+result.model);
   root.append(path);
   for(const point of line.points){
     const selected=point.year===chosenYear;
     root.append(svg("circle",{cx:x(point.year),cy:y(point.probability),r:selected?6.2:4.1,stroke:"#07121c","stroke-width":1.8,fill:color},
       line.country.name+" · "+point.year+": "+pct(point.probability)));
   }
 });
 const inspect=svg("line",{x1:x(chosenYear),y1:t,x2:x(chosenYear),y2:b,stroke:"#d9e7f0","stroke-width":1.2,"stroke-dasharray":"2 7",opacity:.8});
 root.append(inspect);
}
function renderResult(){
 const catalog=current();if(!catalog)return;
 const chosen=[...ids(catalog)];
 try{
   const result=compareHistoricalCountries(catalog,chosen,$("comparison-model").value,$("comparison-question").value);
   if(!result.years.includes(chosenYear))chosenYear=result.years[0];
   const yearSelect=$("comparison-year");yearSelect.replaceChildren();
   for(const year of result.years){
     const option=document.createElement("option");option.value=String(year);option.textContent=String(year);option.selected=year===chosenYear;yearSelect.append(option);
   }
   const legend=$("comparison-legend");legend.replaceChildren();
   result.series.forEach((s,i)=>{
     const chip=el("span"),stripe=el("i");
     stripe.style.borderColor=COLORS[i];stripe.style.borderTopStyle=i===0?"solid":i%2?"dashed":"dotted";
     chip.append(stripe,el("strong",s.country.name));legend.append(chip);
   });
   drawChart(result);
   const tableRoot=$("comparison-table"),statesRoot=$("comparison-states");
   tableRoot.replaceChildren();statesRoot.replaceChildren();
   const table=el("table",undefined,"country-table"),caption=el("caption","Resultados retrospectivos por país · "+chosenYear);
   const head=document.createElement("thead"),header=document.createElement("tr");
   for(const h of ["País","Probabilidad","Diferencia respecto al mayor"])header.append(el("th",h));
   head.append(header);table.append(caption,head);
   const body=document.createElement("tbody");
   const points=result.series.map((line,i)=>({line,i,p:line.points.find(p=>p.year===chosenYear)}));
   const max=Math.max(...points.map(x=>x.p.probability));
   for(const {line,i,p} of points){
     const row=document.createElement("tr");
     const country=el("td",line.country.name);country.style.color=COLORS[i];
     row.append(country,el("td",pct(p.probability)),el("td",pct(max-p.probability)));
     body.append(row);
     const card=el("article");card.append(el("h3",line.country.name+" · "+chosenYear));
     p.distribution.forEach((prob,state)=>card.append(el("p",FOUR_STATES[state]+": "+pct(prob))));
     statesRoot.append(card);
   }
   table.append(body);tableRoot.append(table);
   const min=Math.min(...points.map(x=>x.p.probability));
   $("comparison-source-status").textContent=
      catalog.origin+" · "+catalog.countries.length+" países en el catálogo verificado · "+chosen.length+
      " comparados · amplitud entre países "+pct(max-min)+
      ". Cálculo histórico revisado, NO pronóstico emitido ni validación as-of.";
 }catch(err){
   $("comparison-source-status").textContent="Comparación no disponible: "+String(err.message);
 }
}
function renderCatalogSelection(){
 const select=$("comparison-origin"),previous=Number(select.value);select.replaceChildren();
 const values=[...catalogs.values()].sort((a,b)=>a.origin-b.origin);
 for(const c of values){
   const option=document.createElement("option");option.value=c.origin;
   option.textContent="Origen "+c.origin+" · "+c.countries.length+" países · "+c.origin+"–"+(c.origin+c.maxHorizon-1);
   select.append(option);
 }
 if(catalogs.has(previous))select.value=String(previous);
 $("comparison-controls").hidden=!values.length;
 $("comparison-interaction").hidden=!values.length;
 $("comparison-country-search").value="";
 if(values.length){renderList();renderResult();}
}
export function createCountryComparison(){
 $("comparison-origin").addEventListener("change",()=>{chosenYear=null;renderList();renderResult();});
 $("comparison-model").addEventListener("change",renderResult);
 $("comparison-question").addEventListener("change",renderResult);
 $("comparison-country-search").addEventListener("input",renderList);
 $("comparison-year").addEventListener("change",()=>{chosenYear=Number($("comparison-year").value);renderResult();});
 return {
   ingest(json){
     const found=discoverHistoricalCountryCatalogs(json);
     for(const c of found){
       if(catalogs.has(c.origin)&&catalogs.get(c.origin).runId!==c.runId)throw Error("CATALOGO_ORIGEN_CONFLICTIVO");
       catalogs.set(c.origin,c);
     }
     if(found.length)renderCatalogSelection();
     return found.map(x=>({origin:x.origin,countries:x.countries.length,modelCount:COUNTRY_MODELS.length}));
   }
 };
}
