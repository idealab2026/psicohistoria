/** Read-only DEC2026 view. Never calculate or alter issued probabilities. */
export const SHA="540e4327e4b39c78227a28f1fabbf8911ad7a2b9391e7b4bacd1ce4296a295bd";
const MODELS={pool_three:"Combinación de tres señales",country_history:"Historial del país",q1_nonzero:"Actividad reciente",pool_two:"Combinación de dos señales",other_violence:"Violencia no estatal y unilateral",global:"Climatología"};
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const pct=v=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(v);
const norm=s=>String(s).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g,"");
export async function verifyDEC2026(raw,receipt,countries){
 if(typeof raw!=="string"||raw.length>320000||!globalThis.crypto?.subtle)throw Error("Fuente DEC2026 inválida");
 const digest=Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(raw)))).map(x=>x.toString(16).padStart(2,"0")).join("");
 if(digest!==SHA||receipt?.candidate_sha256!==SHA||receipt.status!=="ISSUED_EXPERIMENTAL_UNRESOLVED"||
 receipt.first_public_candidate_at_utc!=="2026-11-24T19:56:40Z"||receipt.document_published_at_utc!=="2026-11-24T19:57:11Z"||
 receipt.first_document_commit!=="e71de1d02908ada1aa8ebcaa8c58c4def1438715"||receipt.candidate_run_id!=="45475399804"||
 receipt.outcomes_resolved!==0||receipt.demonstrated_predictive_skill!==false||receipt.independently_notarized!==false)throw Error("Emisión DEC2026 no autenticada");
 const data=JSON.parse(raw),names=new Map(countries.map(x=>[x.country_id,x.country]));
 if(names.size!==196||countries.length!==196||data.cells.length!==8||data.outcomes_resolved!==0||data.demonstrated_predictive_skill!==false)throw Error("Universo DEC2026 inválido");
 for(const cell of data.cells){
 if(cell.countries.length!==196||new Set(cell.countries.map(x=>x.country_id)).size!==196||cell.countries.some(x=>!names.has(x.country_id)||typeof names.get(x.country_id)!=="string"))throw Error("Correspondencia de países inválida");
 }
 return {data,receipt,names};
}
export function filterDEC2026(doc,{threshold=10,horizon=90,model="pool_three",query="",page=0,includeExcluded=false}={}){
 if(!doc||!Object.hasOwn(MODELS,model))throw Error("Modelo no válido");
 const cell=doc.data.cells.find(x=>x.threshold===Number(threshold)&&x.horizon===Number(horizon));
 if(!cell)throw Error("Escenario no válido");
 const q=norm(query.trim()),all=cell.countries.map(x=>({...x,country:doc.names.get(x.country_id),probability:x.eligible?x.probabilities[model]:null}));
 const rows=all.filter(x=>(includeExcluded||x.eligible)&&(!q||norm(x.country).includes(q)||String(x.country_id)===q)).sort((a,b)=>(b.probability??-1)-(a.probability??-1)||a.country.localeCompare(b.country));
 const pageCount=Math.max(1,Math.ceil(rows.length/20));const selected=Math.min(Math.max(0,Math.trunc(page)||0),pageCount-1);
 const eligible=all.filter(x=>x.eligible),cutoff=eligible.map(x=>x.probability).sort((a,b)=>b-a)[4];
 const above=eligible.filter(x=>x.probability>cutoff).length,tied=eligible.filter(x=>x.probability===cutoff).length;
 return {cell,rows:rows.slice(selected*20,selected*20+20),total:rows.length,page:selected,pageCount,above,tied,slots:5-above,cutoff};
}
export function renderDEC2026(doc,filters={}){
 const header='<header class="section-head"><div class="eyebrow">PREDICCIONES · EMISIÓN EXPERIMENTAL</div><h2>DEC2026 · Alerta a 30 y 90 días</h2><p>Violencia estatal organizada. Probabilidad de alcanzar un umbral de fallecidos codificados por UCDP en la ventana objetivo, entre países con actividad previa inferior a ese umbral.</p></header>';
 if(!doc)return header+'<p class="notice alert">Emisión no disponible o sin verificar. No se muestran probabilidades de respaldo.</p>';
 const t=filters.threshold??10,h=filters.horizon??90,m=filters.model??"pool_three",q=filters.query??"",excluded=filters.includeExcluded??false;
 const f=filterDEC2026(doc,filters),c=f.cell;
 const opts=(values,selected)=>values.map(([v,label])=>'<option value="'+esc(v)+'"'+(String(v)===String(selected)?' selected':'')+'>'+esc(label)+'</option>').join("");
 const stats=[["196","Universo de países"],["1.304","País-escenarios elegibles"],["7.824","Probabilidades (6 modelos)"],["0","Resultados resueltos"]].map(([v,l])=>'<div><strong>'+v+'</strong><span>'+l+'</span></div>').join("");
 return header+'<div class="prospective-stats">'+stats+'</div>'+
 '<section class="panel"><h3>Explorar predicciones</h3><div class="prospective-controls">'+
 '<label>Umbral <select id="dec2026-threshold">'+opts([1,5,10,25].map(x=>[x,"≥ "+x+" fallecidos"]),t)+'</select></label>'+
 '<label>Horizonte <select id="dec2026-horizon">'+opts([[30,"30 días"],[90,"90 días"]],h)+'</select></label>'+
 '<label>Modelo <select id="dec2026-model">'+opts(Object.entries(MODELS),m)+'</select></label>'+
 '<label>País <input type="search" id="dec2026-query" maxlength="120" value="'+esc(q)+'" placeholder="Nombre oficial o código"></label>'+
 '<button class="ghost" data-action="dec2026-search" data-value="buscar">Buscar</button>'+
 '<label><input type="checkbox" id="dec2026-excluded"'+(excluded?' checked':'')+'> Incluir no elegibles</label></div>'+
 '<p class="tiny">'+esc(c.target_start)+' — '+esc(c.target_end)+' · '+c.n_eligible+' elegibles / 196 · '+c.n_train+' observaciones de entrenamiento · '+f.total+' coincidencias</p>'+
 '<p class="notice info">Presupuesto de 5 alertas: '+f.above+' países por encima del corte y '+f.tied+' empatados para '+f.slots+' plazas. No se selecciona arbitrariamente entre empates. El orden alfabético es solo visual.</p>'+
 '<div class="prospective-table-wrap"><table class="prospective-table"><thead><tr><th>País</th><th>Probabilidad</th><th>Climatología</th><th>Estado / modelos</th></tr></thead><tbody>'+
 f.rows.map(x=>'<tr><td data-label="País"><strong>'+esc(x.country)+'</strong><small>GWNO '+x.country_id+'</small></td><td data-label="Probabilidad"><strong class="prospective-prob">'+(x.eligible?pct(x.probability):"—")+'</strong></td><td data-label="Climatología">'+(x.eligible?pct(x.probabilities.global):"—")+'</td><td data-label="Estado">'+(x.eligible?'<span class="prospective-pending">Sin resolver</span><details><summary>Seis modelos</summary><div class="prospective-alternatives">'+Object.entries(MODELS).map(([k,l])=>'<span>'+esc(l)+' · '+pct(x.probabilities[k])+'</span>').join("")+'</div></details>':'No elegible · sin probabilidad')+'</td></tr>').join("")+
 '</tbody></table></div><div class="prospective-pager"><button class="ghost" data-action="dec2026-page" data-value="'+(f.page-1)+'"'+(!f.page?' disabled':'')+'>Anterior</button><span>Página '+(f.page+1)+' / '+f.pageCount+'</span><button class="ghost" data-action="dec2026-page" data-value="'+(f.page+1)+'"'+(f.page===f.pageCount-1?' disabled':'')+'>Siguiente</button></div></section>'+
 '<section class="panel"><h3>Evidencia y resolución</h3><p>Emisión pública: 24/11/2026, 19:56 UTC. Fuentes: agosto–octubre de 2026; entrenamiento 2021–2023. Resolución con las primeras ediciones anuales GED 27.1 y 28.1, según horizonte.</p><p><a href="./data/forecast-dec2026-pilot.json">Predicciones originales</a> · <a href="./data/forecast-dec2026-pilot-manifest.json">Manifiesto SHA-256</a> · <a href="https://github.com/idealab2026/psicohistoria/actions/runs/45475399804">Ejecución original</a></p><p class="tiny">Hipótesis primaria probabilística: combinación de tres señales, 10 fallecidos / 90 días; ranking primario: historial del país, 5 alertas. Emisión experimental, cambio estacional no validado; sin notarización independiente ni habilidad prospectiva demostrada. No equivale a probabilidad de guerra. Los modelos y escenarios no son observaciones independientes.</p></section>';
}
