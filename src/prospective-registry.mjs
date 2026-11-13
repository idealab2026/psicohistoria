/** Read-only public table of SHA-frozen 2027 GEO, NEWCONF, ACD issues. */
const esc=value=>String(value??"").replace(/[&<>"']/g,c=>({
 "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
const SUFFIX="2027";
export const REGISTRY_SCHEMA="idealab.psico.prospective_2027_issued_registry.v1";
export const COHORT_ORDER=["GEO2027","NEWCONF2027","ACD2027"];
export const ORIGINAL_SHA=Object.freeze({
 GEO2027:"5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5",
 NEWCONF2027:"e4482da7396872645d5101115435143d98fd9fdb1db1b1fdf41a42c99fc04b74",
 ACD2027:"6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c"
});
export const ORIGINAL_COMMITS=Object.freeze({
 GEO2027:"3bb3561c8d6182c30624591276c705fb76ce99dc",
 NEWCONF2027:"f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97",
 ACD2027:"41db7bd154e0140ced15abd8727a7d52d998852c"
});
const EXPECTED_DATE=Object.freeze({
 GEO2027:"2026-11-10T17:23:12Z",
 NEWCONF2027:"2026-11-11T10:10:21Z",
 ACD2027:"2026-11-12T22:24:56Z"
});
const EXPECTED_COUNTS=Object.freeze({GEO2027:196,NEWCONF2027:196,ACD2027:32});
const REGISTRY_ROWS=424;
const n=val=>typeof val==="number"&&Number.isFinite(val);
const probability=v=>n(v)&&v>0&&v<1;
const githubCommit=sha=>"https://github.com/idealab2026/psicohistoria/commit/"+sha;
const pct=v=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(v);
const num=v=>new Intl.NumberFormat("es-ES").format(v);

export function validateProspectiveRegistry(doc){
 if(!doc||doc.schema!==REGISTRY_SCHEMA||
    doc.status!=="PROSPECTIVE_ISSUED_ALL_OUTCOMES_2027_UNRESOLVED"||
    doc.target_year!==2027||doc.n_distinct_issued_endpoints!==3||
    doc.n_unique_country_endpoint_rows!==REGISTRY_ROWS||
    doc.n_verified_future_2027_outcomes!==0||
    doc.n_original_geo_transition_alerts_subset!==15||
    doc.n_original_geo_shadow_comparator_countries!==196||
    doc.observational_skill_demonstrated!==false||
    doc.independent_country_endpoints_or_country_years!==false||
    doc.first_commit_times_are_public_metadata_not_independent_notarization!==true||
    !Array.isArray(doc.cohort_order)||doc.cohort_order.join("|")!==COHORT_ORDER.join("|")||
    !doc.cohorts||Object.keys(doc.cohorts).sort().join("|")!==COHORT_ORDER.slice().sort().join("|")||
    !Array.isArray(doc.rows)||doc.rows.length!==REGISTRY_ROWS)
  throw Error("REGISTRO_PROSPECTIVO_2027_INCOMPLETO");
 const seen=new Set(),counts=Object.fromEntries(COHORT_ORDER.map(c=>[c,0]));
 const alertCount={ENTRADA:0,RESOLUCION:0};
 const sourceKinds=new Set();
 for(const c of COHORT_ORDER){
  const x=doc.cohorts[c];
  if(!x||x.fixed_country_count!==EXPECTED_COUNTS[c]||
     x.forecast_sha256!==ORIGINAL_SHA[c]||
     x.first_public_commit!==ORIGINAL_COMMITS[c]||
     x.issue_utc!==EXPECTED_DATE[c]||
     x.origin_data_through!==2025||
     x.resolution!=="PENDIENTE_FUENTE_ANUAL_OFICIAL_2027"||
     !["p_model","p_global_recent5"].includes(x.primary_model)||
     (c==="ACD2027"?"p_global_recent5":"p_model")!==x.primary_model||
     typeof x.question!=="string"||x.question.length<35||
     typeof x.source!=="string"||x.source.length<15||
     typeof x.evaluation!=="string"||x.evaluation.length<30||
     !/^https:\/\/ucdp\.uu\.se\//.test(x.source_url)||
     !/^[0-9a-f]{64}$/.test(x.source_sha256))
   throw Error("REGISTRO_EMISION_2027_MODIFICADA");
  sourceKinds.add(x.source);
 }
 if(sourceKinds.size!==3)throw Error("TRES_VARIABLES_PROSPECTIVAS_NO_DISTINTAS");
 for(const row of doc.rows){
  if(!row||!COHORT_ORDER.includes(row.cohort)||
     !Number.isInteger(row.country_id)||row.country_id<=0||row.country_id>2000||
     typeof row.country!=="string"||row.country.trim().length<2||row.country.length>110||
     !probability(row.p_primary)||!row.p_secondary||
     typeof row.p_secondary!=="object"||Array.isArray(row.p_secondary)||
     row.issued_status!=="EMITIDA_PENDIENTE"||
     row.resolved_2027!==false||row.observed_2027!==null||
     row.certified_result!==false)
   throw Error("REGISTRO_FILA_2027_INVALIDA");
  const key=row.cohort+":"+row.country_id;
  if(seen.has(key))throw Error("REGISTRO_DUPLICA_VARIABLE_PAIS");
  seen.add(key);counts[row.cohort]++;
  const secondary=Object.keys(row.p_secondary);
  const expected=row.cohort==="GEO2027"?
   ["p_global_markov","p_shadow_exploratorio"]:
   row.cohort==="NEWCONF2027"?["p_baseline_global_5y"]:
   ["p_country_eb_exploratorio","p_lag1_group_exploratorio"];
  if(secondary.slice().sort().join("|")!==expected.sort().join("|")||
     secondary.some(k=>!probability(row.p_secondary[k])))
   throw Error("REGISTRO_COMPARADORES_ALTERADOS");
  if(row.geo_transition_alert!==null){
   if(row.cohort!=="GEO2027"||!["ENTRADA","RESOLUCION"].includes(row.geo_transition_alert))
    throw Error("ALERTA_GEO_CONTADA_FUERA_COHORTE");
   alertCount[row.geo_transition_alert]++;
  }
 }
 if(COHORT_ORDER.some(c=>counts[c]!==EXPECTED_COUNTS[c])||
    alertCount.ENTRADA!==10||alertCount.RESOLUCION!==5)
  throw Error("REGISTRO_DENOMINADORES_2027_CAMBIADOS");
 // The different endpoints must not silently become identical country labels.
 const countryMap=new Map();
 for(const row of doc.rows){
  const name=countryMap.get(row.country_id);
  if(name&&name!==row.country)throw Error("REGISTRO_NOMBRE_PAIS_INCONSISTENTE");
  countryMap.set(row.country_id,row.country);
 }
 if(countryMap.size!==196)throw Error("COBERTURA_PAIS_2027_CAMBIADA");
 return doc;
}

export function filterProspectiveRegistry(doc,{cohort="TODAS",query="",page=0,pageSize=20}={}){
 validateProspectiveRegistry(doc);
 if(cohort!=="TODAS"&&!COHORT_ORDER.includes(cohort))
  throw Error("FILTRO_COHORTE_NO_RECONOCIDO");
 if(typeof query!=="string"||query.length>120)throw Error("CONSULTA_PAIS_NO_VALIDA");
 if(!Number.isInteger(page)||page<0||!Number.isInteger(pageSize)||pageSize<1||pageSize>50)
  throw Error("PAGINACION_REGISTRO_NO_VALIDA");
 const normal=query.trim().toLocaleLowerCase("es-ES").normalize("NFD")
   .replace(/[\u0300-\u036f]/g,"");
 const rows=doc.rows.filter(r=>
  (cohort==="TODAS"||cohort===r.cohort) &&
  (!normal||r.country.toLocaleLowerCase("es-ES").normalize("NFD")
    .replace(/[\u0300-\u036f]/g,"").includes(normal)||
    String(r.country_id)===normal)
 );
 const pageCount=Math.max(1,Math.ceil(rows.length/pageSize));
 const selectedPage=Math.min(page,pageCount-1);
 return {rows:rows.slice(selectedPage*pageSize,(selectedPage+1)*pageSize),
         total:rows.length,page:selectedPage,pageCount,pageSize};
}

export function renderProspectiveRegistry(doc,filters={}){
 if(!doc)return '<header class="section-head"><h2>Registro prospectivo 2027</h2>'+
    '<p>Registro no disponible o sin verificar. No se presentan cifras de respaldo.</p></header>';
 validateProspectiveRegistry(doc);
 const c=filters.cohort??"TODAS",q=filters.query??"",page=filters.page??0;
 const result=filterProspectiveRegistry(doc,{cohort:c,query:q,page});
 const issueLinks=COHORT_ORDER.map(id=>{
  const d=doc.cohorts[id];
  return '<div class="prospective-cohort-card"><div class="eyebrow">'+esc(id)+'</div>'+
   '<strong>'+d.fixed_country_count+' países</strong>'+
   '<p>'+esc(d.question)+'</p>'+
   '<div class="tiny">Emitida: '+esc(d.issue_utc.slice(0,10))+' · Fuente: '+esc(d.source)+'</div>'+
   '<a href="'+githubCommit(d.first_public_commit)+'" target="_blank" rel="noopener noreferrer">'+
   'Primera emisión verificada</a></div>';
 }).join("");
 const options=[["TODAS","Todas las variables (424)"],...COHORT_ORDER.map(id=>
  [id,id+" ("+doc.cohorts[id].fixed_country_count+")"])].map(([id,text])=>
  '<option value="'+id+'"'+(id===c?' selected':'')+'>'+esc(text)+'</option>').join("");
 const header='<header class="section-head"><div class="eyebrow">PREDICCIONES · EMISIONES REALES</div>'+
  '<h2>Registro prospectivo de 2027</h2>'+
  '<p>Tres variables distintas y 424 predicciones país-variable emitidas antes del resultado. '+
  'No son 424 países independientes ni resultados acertados. Todas siguen abiertas.</p></header>';
 const summary='<div class="prospective-stats">'+[
  ["3","Cohortes con objetivo definido"],
  ["424","País-variable emitidos"],
  ["15","Alertas GEO incluidas, no adicionales"],
  ["0","Resultados de 2027 verificados"]
 ].map(([v,label])=>'<div><strong>'+v+'</strong><span>'+esc(label)+'</span></div>').join("")+'</div>';
 const table='<div class="prospective-controls">'+
  '<label>Variable <select id="prospective-cohort" aria-label="Filtrar por variable">'+options+'</select></label>'+
  '<label>País <input id="prospective-query" type="search" maxlength="120" autocomplete="off" placeholder="Buscar país o código" value="'+esc(q)+'"></label>'+
  '<button type="button" class="ghost" data-action="prospective-search" data-value="buscar">Buscar</button></div>'+
  '<p class="tiny" role="status">'+num(result.total)+' registros coincidentes · Página '+
  (result.page+1)+' de '+result.pageCount+'. La probabilidad mostrada es del modelo primario correspondiente.</p>'+
  '<div class="prospective-table-wrap"><table class="prospective-table">'+
  '<thead><tr><th>Variable / pregunta</th><th>País</th><th>Probabilidad</th>'+
  '<th>Primera emisión</th><th>Fuente oficial</th><th>Estado / detalle</th></tr></thead><tbody>'+
  result.rows.map(r=>{
   const d=doc.cohorts[r.cohort];
   const explanation=Object.entries(r.p_secondary).map(([model,value])=>
    '<span>'+esc(model.replaceAll("_"," "))+' · '+pct(value)+'</span>').join("");
   return '<tr>'+
    '<td data-label="Pregunta"><strong>'+esc(r.cohort)+'</strong>'+
    (r.geo_transition_alert?' <span class="prospective-alert">Alerta '+esc(r.geo_transition_alert.toLowerCase())+'</span>':'')+
    '<small>'+esc(d.question)+'</small></td>'+
    '<td data-label="País"><strong>'+esc(r.country)+'</strong><small>GWNO '+r.country_id+'</small></td>'+
    '<td data-label="Probabilidad"><strong class="prospective-prob">'+pct(r.p_primary)+'</strong>'+
    '<small>Modelo primario · '+esc(d.primary_model.replaceAll("_"," "))+'</small></td>'+
    '<td data-label="Primera emisión">'+esc(d.issue_utc.slice(0,10))+
    '<small><a href="'+githubCommit(d.first_public_commit)+'" target="_blank" rel="noopener noreferrer">Commit público</a></small></td>'+
    '<td data-label="Fuente">'+esc(d.source)+
    '<small><a href="'+esc(d.source_url)+'" target="_blank" rel="noopener noreferrer">Fuente UCDP</a></small></td>'+
    '<td data-label="Estado"><span class="prospective-pending">Sin resultado 2027</span>'+
    '<details><summary>Otros modelos</summary><div class="prospective-alternatives">'+explanation+
    '</div><p class="tiny">Comparadores exploratorios, no nuevos resultados ni pruebas de superioridad.</p></details></td>'+
    '</tr>';
  }).join("")+'</tbody></table></div>'+
  '<div class="prospective-pager"><button type="button" class="ghost" data-action="prospective-page" data-value="'+(result.page-1)+'"'+(result.page===0?' disabled':'')+'>Anterior</button>'+
  '<span>Página '+(result.page+1)+' / '+result.pageCount+'</span>'+
  '<button type="button" class="ghost" data-action="prospective-page" data-value="'+(result.page+1)+'"'+(result.page>=result.pageCount-1?' disabled':'')+'>Siguiente</button></div>';
 return header+summary+'<div class="prospective-cohorts">'+issueLinks+'</div>'+
  '<section class="panel"><h3>Predicciones individuales</h3>'+table+'</section>'+
  '<p class="notice info">Las probabilidades GEO, NEWCONF y ACD miden eventos diferentes; nunca se promedian ni se suman como si fueran la misma predicción. '+
  'El modelo shadow y las 15 alertas GEO son comparadores o selecciones de emisiones existentes, no nuevas cohortes. '+
  'Las fechas son metadatos públicos de GitHub, no sellos notariales independientes.</p>';
}
