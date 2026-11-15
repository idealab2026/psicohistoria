/** Read-only view of the separately SHA-verified original 196-country GEO2028 issue.
 * NOT an additional 2027 endpoint. Same 2025 origin as GEO2027; dependent.
 */
export const GEO2028_FORECAST_SHA="fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde";
export const GEO2028_FIRST_COMMIT="5a7c949f6fe9a352ecb27c4e4193f2f3e92b64d0";
export const GEO2028_FIRST_UTC="2026-11-15T18:27:05Z";
export const GEO2028_PROTOCOL_COMMIT="83c1be9a03f31c38993350b26ff0ff1e678cb0c5";
export const GEO2027_FORECAST_SHA="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5";
export const GEO_SOURCE_SHA="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34";
export const GEO2028_ID="PSICO-GEO2028-STATEBASED25-H3-ORIGIN2025-V1";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({
 "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
const isProbability=p=>typeof p==="number"&&Number.isFinite(p)&&p>0&&p<1;
const pct=v=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(v);
const dec=v=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2}).format(v);
const normalize=s=>String(s).trim().toLocaleLowerCase("es-ES").normalize("NFD")
  .replace(/[\u0300-\u036f]/g,"");
const linkToCommit=sha=>"https://github.com/idealab2026/psicohistoria/commit/"+sha;

export function validateIssuedGEO2028(doc,manifest,original2027){
 if(!doc||!manifest||!original2027||
    doc.schema!=="idealab.psico.prospective_geo2028_three_year.v1"||
    doc.forecast_id!==GEO2028_ID||
    doc.state!=="CANDIDATE_BEFORE_FIRST_PUBLIC_2028_ISSUE"||
    doc.target?.year!==2028||
    doc.origin?.year!==2025||doc.origin?.official_data_last_year!==2025||
    doc.origin?.source_version!=="26.1"||
    doc.origin?.official_sha256!==GEO_SOURCE_SHA||
    doc.origin?.official_url!=="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip"||
    doc.origin?.same_2025_origin_as_GEO2027!==true||
    doc.protocol?.horizon_years!==3||
    doc.protocol?.primary_model!=="country_markov_3step_laplace_global_shrink20"||
    doc.protocol?.primary_baseline!=="global_laplace_5y_2021_2025"||
    doc.protocol?.secondary_comparator!=="global_markov_3step_laplace"||
    doc.protocol?.not_independent_rolling_origin_two_year_replication!==true||
    doc.protocol?.cannot_pool_with_GEO2027_as_independent_forecasts!==true||
    doc.protocol?.no_automatic_promotion_or_model_selection!==true||
    doc.first_issue_provenance?.original_GEO2027_SHA256!==GEO2027_FORECAST_SHA||
    doc.first_issue_provenance?.original_GEO2027_first_public_commit!=="3bb3561c8d6182c30624591276c705fb76ce99dc"||
    doc.first_issue_provenance?.independent_timestamp_notary!==false||
    doc.first_issue_provenance?.official_2028_outcomes_observed!==0||
    doc["2028_outcomes_resolved"]!==0||
    doc.prospective_predictive_skill_demonstrated!==false||
    doc.n_countries!==196||!Array.isArray(doc.countries)||doc.countries.length!==196)
  throw Error("GEO2028_PRONOSTICO_ORIGINAL_NO_VERIFICADO");
 const requiredManifest={
  schema:"idealab.psico.geo2028_three_year_first_public_attestation.v1",
  status:"ISSUED_PROSPECTIVE_THREE_YEAR_UNRESOLVED",
  forecast_file:"data/forecast-2028-geo3.json",
  forecast_id:GEO2028_ID,
  forecast_sha256:GEO2028_FORECAST_SHA,
  first_public_forecast_commit:GEO2028_FIRST_COMMIT,
  first_public_forecast_commit_utc:GEO2028_FIRST_UTC,
  first_public_commit_added_file:true,
  preregistered_protocol_pr:75,
  preregistered_protocol_main_commit:GEO2028_PROTOCOL_COMMIT,
  origin_source_sha256:GEO_SOURCE_SHA,
  origin_last_year:2025,
  target_year:2028,
  horizon_years:3,
  n_issued_country_probabilities:196,
  primary_model:"p_model",
  primary_baseline:"p_baseline_global_5y",
  comparator_markov_global:"p_global_markov_3step",
  original_GEO2027_first_public_sha256:GEO2027_FORECAST_SHA,
  original_GEO2027_issuance_unchanged:true,
  cross_horizon_2027_2028_outcomes_statistically_independent:false,
  independently_notarized:false,
  GitHub_commit_time_is_public_metadata_not_independent_notary:true,
  actual_2028_outcomes_observed:0,
  prospective_predictive_skill_demonstrated:false,
  operator_declared_first_complete_2028_official_source_verified:false,
  new_2028_TWO_year_origin_2026_forecast_included:false
 };
 for(const [k,v] of Object.entries(requiredManifest))
  if(manifest[k]!==v)throw Error("GEO2028_MANIFIESTO_DE_EMISION_MODIFICADO");
 if(original2027.schema!=="idealab.psico.prospective_2027_issued_registry.v1"||
    original2027.target_year!==2027||
    original2027.n_unique_country_endpoint_rows!==424||
    original2027.n_verified_future_2027_outcomes!==0||
    original2027.cohorts?.GEO2027?.forecast_sha256!==GEO2027_FORECAST_SHA)
  throw Error("GEO2027_REGISTRO_ORIGINAL_NO_VERIFICADO");
 const oldRows=original2027.rows.filter(r=>r.cohort==="GEO2027");
 if(oldRows.length!==196)throw Error("GEO2027_PAÍSES_INCOMPLETOS");
 const oldMap=new Map(oldRows.map(r=>[r.country_id,r]));
 if(oldMap.size!==196)throw Error("GEO2027_IDS_DUPLICADOS");
 const ids=new Set();
 let last=-1,totals={p_model:0,p_global_markov_3step:0,p_baseline_global_5y:0};
 for(const row of doc.countries){
  if(!row||!Number.isInteger(row.country_id)||row.country_id<=last||
     row.country_id>2000||ids.has(row.country_id)||
     typeof row.country!=="string"||row.country.length<2||row.country.length>110||
     ![0,1].includes(row.last_observed_state_2025)||
     !isProbability(row.p_model)||!isProbability(row.p_global_markov_3step)||
     !isProbability(row.p_baseline_global_5y)||
     !isProbability(row.p_issued_geo2027_2step_for_temporal_comparison_only))
   throw Error("GEO2028_FILA_EMITIDA_INVALIDA");
  ids.add(row.country_id);last=row.country_id;
  const old=oldMap.get(row.country_id);
  if(!old||old.country!==row.country||
     old.p_primary!==row.p_issued_geo2027_2step_for_temporal_comparison_only)
   throw Error("GEO2028_MODIFICA_IDENTIDAD_O_PROBABILIDAD_GEO2027");
  for(const key of Object.keys(totals))totals[key]+=row[key];
 }
 if(ids.size!==196)throw Error("GEO2028_CONJUNTO_DE_RIESGO_INCOMPLETO");
 if(!doc.model_expected_2028_active_countries||
    Object.keys(doc.model_expected_2028_active_countries).sort().join("|")!==
     Object.keys(totals).sort().join("|")||
    Object.keys(totals).some(key=>
      Math.abs(totals[key]-doc.model_expected_2028_active_countries[key])>1e-10))
  throw Error("GEO2028_TOTAL_PROBABILISTICO_ALTERADO");
 return doc;
}

export function filterGEO2028(doc,manifest,original2027,{
 query="",order="risk",page=0,pageSize=20
}={}){
 validateIssuedGEO2028(doc,manifest,original2027);
 if(typeof query!=="string"||query.length>120||
    !["risk","country","change"].includes(order)||
    !Number.isInteger(page)||page<0||
    !Number.isInteger(pageSize)||pageSize<1||pageSize>50)
  throw Error("GEO2028_FILTROS_INVALIDOS");
 const norm=normalize(query);
 const matches=doc.countries.filter(r=>!norm||
   normalize(r.country).includes(norm)||String(r.country_id)===norm);
 const sorted=[...matches].sort((a,b)=>{
  if(order==="country")return a.country.localeCompare(b.country,"es");
  if(order==="change"){
   const deltaA=a.p_model-a.p_issued_geo2027_2step_for_temporal_comparison_only;
   const deltaB=b.p_model-b.p_issued_geo2027_2step_for_temporal_comparison_only;
   return Math.abs(deltaB)-Math.abs(deltaA)||a.country_id-b.country_id;
  }
  return b.p_model-a.p_model||a.country_id-b.country_id;
 });
 const total=sorted.length,pageCount=Math.max(1,Math.ceil(total/pageSize));
 const safePage=Math.min(page,pageCount-1);
 return {rows:sorted.slice(safePage*pageSize,(safePage+1)*pageSize),
         total,page:safePage,pageCount};
}

export function renderGEO2028(doc,manifest,original2027,filters={}){
 if(!doc||!manifest||!original2027){
  return '<header class="section-head"><h2>GEO2028 · Horizonte tres años</h2>'+
   '<p>La emisión no se puede verificar. No se presentan probabilidades sin autenticar.</p></header>'+
   '<p class="notice info">El registro GEO2027 permanece disponible por separado.</p>';
 }
 validateIssuedGEO2028(doc,manifest,original2027);
 const query=filters.query??"",order=filters.order??"risk",page=filters.page??0;
 const results=filterGEO2028(doc,manifest,original2027,{query,order,page});
 const t=doc.model_expected_2028_active_countries;
 const stats=[
  ["196","Países GWNO con pronóstico"],
  [dec(t.p_model),"Países activos esperados · modelo"],
  [dec(t.p_baseline_global_5y),"Países esperados · referencia"],
  ["0","Resultados oficiales de 2028"]
 ].map(([v,l])=>'<div><strong>'+esc(v)+'</strong><span>'+esc(l)+'</span></div>').join("");
 const sorts=[["risk","Mayor probabilidad"],["country","País A–Z"],["change","Mayor cambio respecto a 2027"]]
  .map(([id,text])=>'<option value="'+id+'"'+(order===id?' selected':'')+'>'+esc(text)+'</option>').join("");
 const table='<div class="prospective-controls">'+
  '<label>País o GWNO <input id="geo2028-query" type="search" maxlength="120" autocomplete="off" placeholder="Buscar país" value="'+esc(query)+'"></label>'+
  '<label>Orden <select id="geo2028-order" aria-label="Ordenar predicciones GEO2028">'+sorts+'</select></label>'+
  '<button class="ghost" type="button" data-action="geo2028-search" data-value="buscar">Buscar</button></div>'+
  '<p class="tiny" role="status">'+results.total+' países coincidentes · Página '+(results.page+1)+' / '+results.pageCount+'</p>'+
  '<div class="prospective-table-wrap"><table class="prospective-table geo2028-table">'+
  '<thead><tr><th>País</th><th>2028 · Modelo</th><th>2027 · Modelo original</th>'+
  '<th>Variación en puntos porcentuales</th><th>Comparadores 2028</th><th>Estado</th></tr></thead><tbody>'+
  results.rows.map(r=>{
   const delta=100*(r.p_model-r.p_issued_geo2027_2step_for_temporal_comparison_only);
   const signed=(delta>0?"+":"")+dec(delta)+" pp";
   return '<tr>'+
    '<td data-label="País"><strong>'+esc(r.country)+'</strong><small>GWNO '+r.country_id+' · Estado 2025: '+(r.last_observed_state_2025?'Activo':'No activo')+'</small></td>'+
    '<td data-label="2028"><strong class="prospective-prob">'+pct(r.p_model)+'</strong><small>Markov país · 3 pasos</small></td>'+
    '<td data-label="2027"><strong>'+pct(r.p_issued_geo2027_2step_for_temporal_comparison_only)+'</strong><small>Emisión 2027 intacta · 2 pasos</small></td>'+
    '<td data-label="Cambio">'+esc(signed)+'<small>Horizontes distintos; no es una mejora validada</small></td>'+
    '<td data-label="Referencias"><details><summary>Comparar</summary><div class="prospective-alternatives">'+
    '<span>Markov global (3): '+pct(r.p_global_markov_3step)+'</span>'+
    '<span>Prevalencia global 2021–25: '+pct(r.p_baseline_global_5y)+'</span>'+
    '</div></details></td>'+
    '<td data-label="Estado"><span class="prospective-pending">Sin resultado 2028</span></td></tr>';
  }).join("")+'</tbody></table></div>'+
  '<div class="prospective-pager">'+
  '<button class="ghost" type="button" data-action="geo2028-page" data-value="'+(results.page-1)+'"'+(results.page===0?' disabled':'')+'>Anterior</button>'+
  '<span>Página '+(results.page+1)+' / '+results.pageCount+'</span>'+
  '<button class="ghost" type="button" data-action="geo2028-page" data-value="'+(results.page+1)+'"'+(results.page===results.pageCount-1?' disabled':'')+'>Siguiente</button></div>';
 return '<header class="section-head"><div class="eyebrow">PREDICCIONES · EMISIÓN VERIFICADA · OBJETIVO 2028</div>'+
  '<h2>GEO2028 · Violencia estatal ≥25 muertes</h2>'+
  '<p>¿Qué países registrarán al menos 25 muertes anuales de violencia organizada estatal en 2028? '+
  'Origen 2025, horizonte de tres años. La tabla muestra <strong>probabilidades emitidas</strong>, no resultados.</p></header>'+
  '<div class="prospective-stats">'+stats+'</div>'+
  '<div class="prospective-cohorts"><div class="prospective-cohort-card">'+
  '<strong>Emisión prospectiva 2028</strong><p>196 países · primer commit: 15/11/2026.</p>'+
  '<a href="'+linkToCommit(GEO2028_FIRST_COMMIT)+'" target="_blank" rel="noopener noreferrer">Ver primera emisión pública</a></div>'+
  '<div class="prospective-cohort-card"><strong>Horizonte 2025 → 2028</strong>'+
  '<p>Tres pasos del modelo Markov entrenado con UCDP 26.1 hasta 2025. Sin datos de origen 2026.</p>'+
  '<a href="'+linkToCommit(GEO2028_PROTOCOL_COMMIT)+'" target="_blank" rel="noopener noreferrer">Protocolo previo a la emisión</a></div>'+
  '<div class="prospective-cohort-card"><strong>Comparación responsable</strong>'+
  '<p>GEO2027 y GEO2028 comparten origen y países; no son réplicas independientes. El Brier 2028 aún no existe.</p>'+
  '<a href="'+linkToCommit("acc8d94265a2adeda5a33cd0cadacb9ffa3f1452")+'" target="_blank" rel="noopener noreferrer">Integridad institucional</a></div></div>'+
  '<section class="panel"><h3>Predicciones por país · 2028 frente a 2027</h3>'+table+'</section>'+
  '<p class="notice info">Las probabilidades 2027 y 2028 se refieren a <strong>años diferentes</strong>. '+
  'Una variación no significa que el riesgo real haya aumentado o disminuido. '+
  'Los 196 registros GEO2028 se añaden a las 424 preguntas de 2027: son 620 cuestiones emitidas, '+
  '<strong>no 620 pruebas independientes</strong>. La fecha del commit es metadato público, no notarización independiente.</p>';
}
