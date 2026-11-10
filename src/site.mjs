import {verify,score,calibration} from "./metrics.mjs";
import {verifyResearch,verifyIssuedForecast2027,parseForecastCSV,evaluateLocalForecast,CSV_TEMPLATE} from "./research.mjs";
import {domainGraph} from "./visuals.mjs";
import {loadProjectCatalog} from "./project-catalog.mjs";
import {renderHistoricalProjectPortfolio} from "./project-portfolio.mjs";
import {scientificNeuralPanel,enableScientificNeural,scientificMarkovPanel,syntheticFourStateModel} from "./lab-renderers.mjs";
import {renderHistoricalTree,acceptPublicCountryCatalogs,setCountrySourceError,getHistoricalCatalog} from "./main-country-tree.mjs";

const $=id=>document.getElementById(id);
const safe=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const format=n=>typeof n==="number"&&Number.isFinite(n)?new Intl.NumberFormat("es-ES",{maximumFractionDigits:3}).format(n):"—";
const formatPct=n=>typeof n==="number"&&Number.isFinite(n)?format(n*100)+" %":"—";
const groupViews={
 brief:[["brief","Inicio"]],
 predictions:[["futures","Explorador"],["shadow2027","Riesgos 2027"]],
 research:[["questions","Preguntas útiles"],["archive","Archivo científico"],["overview","Mapa del proyecto"],["registry","Líneas y fuentes"],["science","Evidencia"],["operations","Registro"],["roadmap","Hitos"]],
 create:[["portfolio","Catálogo recuperado"],["ideas","Nuevas ideas"],["video","Estudio audiovisual"]]
};
const viewIds=new Set(Object.values(groupViews).flat().map(x=>x[0]));
const viewToGroup=Object.fromEntries(Object.entries(groupViews).flatMap(([k,items])=>items.map(([id])=>[id,k])));
const state={archive:null,projectCatalog:null,archiveTable:0,archiveQuery:"",archivePage:0,data:null,research:null,registryFilter:"todos",registryOutput:null,questionPriority:"P1",view:viewIds.has(new URLSearchParams(location.search).get("view"))?new URLSearchParams(location.search).get("view"):"brief",scenario:null,program:null,study:null,filter:"todos",ideas:[],flowState:"00",markovOrigin:2020,markovHorizon:6,markovQuestion:"atleast25",markovSelection:null,countryTreeOrigin:2020,countryTreeId:null,countryTreeModel:"country_shrinkage",countryTreeQuestion:"atleast25",countryTreeYear:null,countryTreeSelection:null,videoText:"",forecastCountryId:null,prospective2027:null,prospective2027Manifest:null,busy:false};
const section=(eyebrow,title,description)=>'<header class="section-head"><div class="eyebrow">'+safe(eyebrow)+'</div><h2>'+safe(title)+'</h2><p>'+safe(description)+'</p></header>';
const box=(contents,extra="")=>'<article class="panel '+extra+'">'+contents+'</article>';
const tag=(t,cls="")=>'<span class="tag '+cls+'">'+safe(t)+'</span>';
const msg=(text,type="info")=>'<div class="notice '+type+'">'+safe(text)+'</div>';
const button=(title,action,value,cls="ghost")=>'<button type="button" class="'+cls+'" data-action="'+safe(action)+'" data-value="'+safe(value)+'">'+safe(title)+'</button>';
const percentageBar=n=>'<div class="barline" aria-label="Peso supuesto: '+safe(Math.round(n*100))+' %"><i style="width:'+Math.round(n*100)+'%"></i></div>';
const syntheticWarning=()=>msg("DATOS SINTÉTICOS: los ejemplos, probabilidades y desenlaces se han creado para comprobar la interfaz. No proceden de una investigación o predicción real.");
const methods=()=>'<div class="section-grid three">'+[
 ["Definir antes de observar","Fijar evento, población, horizonte temporal y regla de evaluación antes de conocer la respuesta."],
 ["Documentar lo disponible","Verificar la edición de cada dato y su fecha de publicación, evitando revisiones posteriores."],
 ["Comparar y reconocer límites","Presentar baseline, cobertura, incertidumbre, errores y resultados no favorables."]
].map(([t,p])=>box('<h3>'+safe(t)+'</h3><p>'+safe(p)+'</p>')).join("")+'</div>';
const cards=items=>'<div class="section-grid">'+items.map(([title,body,action,value])=>box('<h3>'+safe(title)+'</h3><p>'+safe(body)+'</p>'+button("Explorar",action,value))).join("")+'</div>';
const programCard=p=>box('<div class="item-row wrap"><h3>'+safe(p.name)+'</h3>'+tag(p.state)+'</div><p>'+safe(p.summary)+'</p><div class="tiny">Criterio metodológico</div><p>'+safe(p.protocol)+'</p>'+button("Examinar línea","program",p.id,p.id===state.program?"ghost active":"ghost"));
// Public structure is intentionally independent from private research cells.
// Never fetch, bundle or link raw scientific registers from a public website.
const PUBLIC_RECORD_COUNTS=Object.freeze([
 ["Hitos",21],["Indicadores",23],["Experimentos",164],
 ["Inscripciones experimentales",1177],["Fases",57],
 ["Avances de investigación",174],["Variables",13],
 ["Eventos",2],["Fuentes de eventos",2],
 ["Calendario",9],["Comparativas externas",193]
]);
function renderArchive(){
 const counts=PUBLIC_RECORD_COUNTS.reduce((n,row)=>n+row[1],0);
 return '<h2>Archivo científico · estructura pública</h2>'+
 '<p>La web pública presenta únicamente el inventario agregado. Los registros completos, textos de investigación y sus fuentes no se publican aquí ni se ofrecen para descarga. Las inscripciones experimentales no acreditan aciertos ni resultados prospectivos.</p>'+
 '<div class="section-grid three">'+PUBLIC_RECORD_COUNTS.map(([name,total])=>
 box('<div class="card-number">'+total+'</div><h3>'+safe(name)+'</h3>')).join("")+
 '</div><p class="tiny">'+PUBLIC_RECORD_COUNTS.length+
 ' categorías · '+counts+' registros históricos inventariados. Acceso al contenido íntegro restringido a entornos autorizados.</p>';
}
function renderBrief(){
 const d=state.data;
 const ready=d.milestones.filter(x=>x.state==="verificado").length;
 return section("INICIO · ESTADO PÚBLICO","Próximos pasos y resultados","Preparar, publicar y demostrar utilidad son hitos distintos. La sección Evidencia incluye estudios reales retrospectivos; otras vistas utilizan muestras sintéticas y no acreditan capacidad prospectiva.")+
 scientificNeuralPanel(d.programs,state.program)+
 box('<div class="item-row wrap"><div><h3>Registro público experimental</h3><p>Fuente real de emisión GEO-2027, resultados aún desconocidos; demostraciones sintéticas separadas.</p></div>'+tag("1 cohorte 2027 · sin resultados","alert")+'</div>'+
 '<div class="section-grid three"><div><div class="card-number">'+d.programs.length+'</div><div class="tiny">Líneas de estudio</div></div><div><div class="card-number">'+ready+'/'+d.milestones.length+'</div><div class="tiny">Pasos técnicos verificados</div></div><div><div class="card-number">1</div><div class="tiny">Cohorte prospectiva emitida · sin evaluar</div></div></div>','highlight')+
 section("LECTURA RÁPIDA","Qué se puede explorar","Cada módulo tiene un propósito concreto y muestra los supuestos, las fuentes y las limitaciones de los ejemplos.")+
 cards([
 ["Árbol de futuros","Escenarios alternativos y supuestos explícitos. No son pronósticos.", "navigate","futures"],
 ["Evidencia y modelos","Estudios retrospectivos reales separados de evaluaciones sintéticas.", "navigate","science"],
 ["Programa de investigación","Mapa de líneas, protocolo, hitos y bloqueos.", "navigate","overview"],
 ["Catálogo recuperado","Cuatro vertientes, tres aplicaciones y catorce relaciones en un registro histórico.", "navigate","portfolio"],
 ["Crear investigaciones","Conectar hipótesis y preparar ideas y guiones locales.", "navigate","ideas"]
 ])+syntheticWarning()+section("CRITERIOS","De la exploración a la evidencia","Qué deberá comprobarse antes de publicar datos o afirmaciones reales.")+methods();
}
function renderFutures(){
 return section("PREDICCIONES · EXPLORADOR","Árbol de predicciones","Escoge una sociedad, la pregunta que quieres calcular y el año. El árbol se actualiza automáticamente con datos oficiales de UCDP.")+
  renderHistoricalTree(state);
}
function renderShadow(){
 const d=state.prospective2027,m=state.prospective2027Manifest;
 if(!d||!m)return section("PREDICCIONES · GEO-2027","Registro prospectivo","No ha podido verificarse el documento emitido. Se ocultan las puntuaciones mientras no sea posible comprobar su procedencia.")+
   msg("Registro 2027 no disponible o incompleto: comprobar la publicación institucional.","alert");
 const rows=d.countries;
 const selected=rows.find(r=>String(r.country_id)===String(state.forecastCountryId))||
   rows.find(r=>r.country.toLowerCase()==="spain")||rows[0];
 const listed=[...rows].sort((a,b)=>a.country.localeCompare(b.country,"es"));
 const ranked=[...rows].sort((a,b)=>b.p_model-a.p_model || a.country.localeCompare(b.country,"es")).slice(0,10);
 const pct=n=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(n);
 const decimal=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2,minimumFractionDigits:2}).format(n);
 const sumModel=rows.reduce((n,r)=>n+r.p_model,0);
 const sumGlobal=rows.reduce((n,r)=>n+r.p_baseline_global_5y,0);
 const active2025=rows.filter(r=>r.last_observed_state_2025===1).length;
 const ranges=[[0,.05],[.05,.1],[.1,.2],[.2,.5],[.5,.8],[.8,1]];
 const probabilityBuckets=ranges.map(([lower,upper])=>({
  lower,upper,countries:rows.filter(r=>r.p_model>=lower&&r.p_model<upper).length
 }));
 const options=listed.map(r=>'<option value="'+safe(r.country_id)+'"'+(r.country_id===selected.country_id?' selected':'')+'>'+safe(r.country)+'</option>').join("");
 const firstCommit="https://github.com/idealab2026/psicohistoria/commit/"+m.first_public_forecast_commit;
 const frozenProtocol="https://github.com/idealab2026/psicohistoria/commit/"+m.preregistered_protocol_main_commit;
 return section("PREDICCIONES · PRIMERA EMISIÓN PROSPECTIVA",
  "2027 · ¿Se superarán 25 muertes de violencia organizada state-based?",
  "196 probabilidades publicadas antes del año objetivo. No son predicciones sobre el inicio de una guerra ni sobre violencia gubernamental contra civiles. La capacidad predictiva todavía no está demostrada.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">PAÍSES EN LA EMISIÓN</div><div class="card-number">'+safe(rows.length)+'</div><p>Cohorte fija de la edición UCDP 26.1 (datos hasta 2025).</p>')+
 box('<div class="eyebrow">PREDICCIONES EMITIDAS</div><div class="card-number">1 cohorte</div><p>Publicada el 10-11-2026, por commit institucional verificable.</p>')+
 box('<div class="eyebrow">RESULTADOS OFICIALES 2027</div><div class="card-number">Pendientes</div><p>0 desenlaces evaluados; no hay aciertos certificados.</p>')+
 '</div>'+
 box('<h3>Consultar la predicción congelada de un país</h3>'+
 '<label for="geo2027-country">País (código UCDP):</label> '+
 '<select id="geo2027-country" aria-label="Elegir país para previsión 2027">'+options+'</select>'+
 '<div class="section-grid three">'+
 '<div><div class="tiny">Modelo prospectivo · '+safe(selected.country)+'</div><div class="card-number">'+pct(selected.p_model)+'</div></div>'+
 '<div><div class="tiny">Referencia global 2021–2025</div><div class="card-number">'+pct(selected.p_baseline_global_5y)+'</div></div>'+
 '<div><div class="tiny">Referencia Markov global</div><div class="card-number">'+pct(selected.p_global_markov)+'</div></div>'+
 '</div>'+
 '<p>Estado de 2025 para esta variable: '+(selected.last_observed_state_2025===1?'al menos 25 fallecimientos estimados':'menos de 25 fallecimientos estimados')+'. Horizonte: año natural 2027, dos pasos de calendario desde 2025. La emisión se publicó en noviembre de 2026: no implica dos años completos de preaviso operativo.</p>'+
 '<p class="notice info">Probabilidades experimentales, no evaluadas. Este indicador mide muertes registradas en conflictos state-based dentro del país; no predice víctimas civiles ni atribuye necesariamente muertes al Gobierno.</p>','soft')+
 box('<h3>Distribución y control de probabilidades · 2027</h3>'+
 '<div class="section-grid three">'+
 '<div><div class="tiny">Países con el umbral en 2025</div><div class="card-number">'+safe(active2025)+'</div></div>'+
 '<div><div class="tiny">Países esperados por el modelo para 2027</div><div class="card-number">'+decimal(sumModel)+'</div></div>'+
 '<div><div class="tiny">Países esperados por la referencia global</div><div class="card-number">'+decimal(sumGlobal)+'</div></div>'+
 '</div>'+
 '<p>Los valores esperados son <strong>sumas de probabilidades</strong>, no números de países realmente afectados. No representan aciertos ni calibración observada.</p>'+
 '<details><summary>Distribución de los 196 pronósticos emitidos</summary>'+
 '<div class="table-wrap"><table><thead><tr><th>Probabilidad</th><th>Países</th></tr></thead><tbody>'+
 probabilityBuckets.map(v=>'<tr><td>'+pct(v.lower)+'–'+pct(v.upper)+'</td><td>'+safe(v.countries)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p><a href="./data/forecast-2027-audit.json" target="_blank" rel="noopener noreferrer">Ver auditoría independiente con las huellas de reproducción</a>. Se recalculan todas las probabilidades desde la misma fuente UCDP oficial, sin cambiar las 196 emitidas.</p>'+
 '</details>','soft')+
 box('<h3>Diez probabilidades más altas del modelo experimental</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>País</th><th>Pronóstico 2027</th><th>Refer. global</th></tr></thead><tbody>'+
 ranked.map(row=>'<tr><td>'+safe(row.country)+'</td><td>'+pct(row.p_model)+'</td><td>'+pct(row.p_baseline_global_5y)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Clasificación descriptiva de los valores ya emitidos, sin interpretación de causalidad ni demostración de calibración. Pueden existir empates.</p>')+
 box('<h3>Protocolo, huellas y evaluación futura</h3>'+
 '<p>Pregunta registrada: <strong>'+safe(m.question)+'</strong>. Primer compromiso público: '+safe(m.first_public_forecast_commit_utc)+'. La metodología se fijó antes, el '+safe(m.preregistered_at_utc)+'. GitHub no es una autoridad independiente de sellado temporal.</p>'+
 '<p><a href="'+safe(frozenProtocol)+'" target="_blank" rel="noopener noreferrer">Ver el protocolo congelado</a> · <a href="'+safe(firstCommit)+'" target="_blank" rel="noopener noreferrer">Ver primer commit de probabilidades</a></p>'+
 '<p>Archivo emitido SHA-256: <code>'+safe(m.forecast_sha256)+'</code></p>'+
 '<p>Fuente oficial UCDP 26.1 SHA-256: <code>'+safe(m.source_zip_sha256)+'</code>. <a href="'+safe(d.source.url)+'" target="_blank" rel="noopener noreferrer">Descargar fuente oficial</a> · licencia CC BY 4.0.</p>'+
 '<p>La primera edición anual oficial completa que incluya 2027 decidirá las etiquetas. Las ausencias seguirán pendientes, no se convertirán en ceros. Métrica principal: Brier frente a frecuencia global 2021–2025; log-loss y Markov global como controles secundarios.</p>'+
 '<p class="notice info">Estado actual: <strong>EMITIDO · NO EVALUADO</strong>. La emisión es real y anterior al desenlace; su valor predictivo sigue sin demostrar.</p>','soft');
}
function renderOverview(){
 const d=state.data;
 const selected=d.programs.find(x=>x.id===state.program)||d.programs[0];
 return section("INVESTIGACIÓN · ESTRUCTURA","Mapa del proyecto","Líneas independientes conectadas mediante preguntas y controles de validación. La investigación aquí descrita es un programa, no una lista de predicciones confirmadas.")+
 scientificNeuralPanel(d.programs,state.program)+
 box('<div class="tiny">LÍNEA SELECCIONADA</div><h3>'+safe(selected.name)+'</h3><p>'+safe(selected.summary)+'</p><h4>Protocolo de salida</h4><p>'+safe(selected.protocol)+'</p><div class="notice info">Estado: '+safe(selected.state)+'. Cualquier resultado empírico deberá superar una evaluación independiente antes de publicarse.</div>')+
 section("SINERGIAS","Arquitectura del laboratorio","Los estudios estructurales, los modelos de predicción, las simulaciones y la auditoría científica se desarrollan con controles comunes.")+
 methods();
}
function renderStudySelector(){
 return '<label class="field" style="max-width:460px">Estudio sintético <select id="study-selector">'+state.data.studies.map(s=>'<option value="'+safe(s.id)+'" '+(state.study===s.id?'selected':'')+'>'+safe(s.title)+'</option>').join("")+'</select></label>';
}
function renderHistoricalLabelRevisions(){
 const r=state.research?.historical_label_revisions;
 if(!r)return "";
 return section("INVESTIGACIÓN · REVISIÓN DE EDICIONES · UCDP","¿Cambian los acontecimientos históricos entre versiones?",
  "Comparación exacta de las etiquetas de inicio de conflicto onset2, entre UCDP 23.1 y 25.1, para los mismos países-año hasta 2022. No representa una predicción emitida.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">ETIQUETAS HISTÓRICAS COMPARADAS</div><div class="card-number">'+safe(r.observations)+'</div><p>Países-año comunes, 1946–2022.</p>')+
 box('<div class="eyebrow">ETIQUETAS REVISADAS</div><div class="card-number">'+safe(r.labels_flipped)+'</div><p>Una de 0 a 1 y otra de 1 a 0.</p>')+
 box('<div class="eyebrow">POSITIVOS EN AMBAS EDICIONES</div><div class="card-number">'+safe(r.positives_23_1)+'</div><p>Recuento igual; episodios individuales revisados.</p>')+
 '</div>'+
 box('<h3>Dos modificaciones de etiquetas publicadas</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Año</th><th>0 → 1</th><th>1 → 0</th></tr></thead><tbody>'+
 r.changes_by_year.map(v=>'<tr><td>'+safe(v.year)+'</td><td>'+safe(v.flips_zero_to_one)+'</td><td>'+safe(v.flips_one_to_zero)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p><strong>Interpretación:</strong> '+safe(r.note)+'</p>'+
 '<details><summary>Fuentes, huellas y limitaciones</summary>'+
 r.source_urls.map((url,i)=>'<p><a href="'+safe(url)+'" target="_blank" rel="noopener noreferrer">UCDP '+(i===0?'23.1':'25.1')+'</a> · SHA-256 <code>'+safe(r.source_sha256s[i])+'</code></p>').join("")+
 '<p>Contraste reproducible en el expediente institucional. Las fechas de publicación originales no están certificadas criptográficamente. Este hallazgo no acredita skill prospectivo.</p></details>','soft');
}
function renderNewEntryComparator(){
 const x=state.research?.new_entry_2027_comparison;
 if(!x)return "";
 const dec=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:5,maximumFractionDigits:5}).format(n);
 const pct=n=>new Intl.NumberFormat("es-ES",{style:"percent",minimumFractionDigits:1,maximumFractionDigits:2}).format(n);
 const met=[
  ["Markov por país",x.model_brier,x.model_logloss],
  ["Frecuencia directa de entradas a dos años",x.entry_prior_brier,x.entry_prior_logloss],
  ["Markov global",x.global_markov_brier,x.global_markov_logloss]
 ];
 return section("INVESTIGACIÓN · NUEVOS CRUCES DE UMBRAL",
   "¿Se anticipan realmente entradas nuevas?",
   "Evaluamos exclusivamente los países que partían por debajo de 25 muertes por violencia organizada de base estatal: el origen no equivale a inicio de guerra. El baseline específico se calcula solo con registros anteriores a cada corte, pero se eligió después de observar los resultados.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">PAÍSES-AÑO INICIALMENTE POR DEBAJO</div><div class="card-number">'+safe(x.n)+'</div><p>'+safe(x.entries)+' terminan superando las 25 muertes en el año de evaluación</p>')+
 box('<div class="eyebrow">BRIER SKILL VS ENTRADA DIRECTA</div><div class="card-number">'+pct(x.skill_vs_entry_prior)+'</div><p>Mejora descriptiva, intervalo de incertidumbre incluye cero</p>')+
 box('<div class="eyebrow">SOBREESTIMACIÓN DEL NÚMERO DE ENTRADAS</div><div class="card-number">'+pct(x.model_predicted_entry_rate/x.empirical_entry_rate-1)+'</div><p>Probabilidad media '+pct(x.model_predicted_entry_rate)+' frente a frecuencia observada '+pct(x.empirical_entry_rate)+'</p>')+
 '</div>'+
 box('<h3>Modelo congelado frente a referencias pertinentes</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Brier ↓</th><th>Log-loss ↓</th></tr></thead><tbody>'+
 met.map(([name,brier,ll])=>'<tr><td>'+safe(name)+'</td><td>'+dec(brier)+'</td><td>'+dec(ll)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>La mejora Brier por país frente a la tasa directa de entradas es '+pct(x.skill_vs_entry_prior)+
 '. El intervalo exploratorio de diferencia Brier modelo menos referencia ['+
 dec(x.country_bootstrap_95_delta_brier_vs_entry_prior[0])+', +'+
 dec(x.country_bootstrap_95_delta_brier_vs_entry_prior[1])+
 '] <strong>incluye cero</strong>: no está demostrada una ventaja estadísticamente fiable.</p>','soft')+
 box('<h3>¿Qué países señalaba primero el modelo?</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Año evaluado</th><th>Nuevas entradas</th><th>AP (ranking)</th><th>ROC-AUC</th><th>Top 5</th><th>Top 10</th><th>Top 20</th></tr></thead><tbody>'+
 x.folds.map(f=>'<tr><td>'+safe(f.year)+'</td><td>'+safe(f.entries)+' de '+safe(f.n)+'</td><td>'+pct(f.ap_model)+'</td><td>'+dec(f.roc_auc_model)+'</td><td>'+safe(f.top_5_hits)+'/5</td><td>'+safe(f.top_10_hits)+'/10</td><td>'+safe(f.top_20_hits)+'/20</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>La precisión promedio (AP) mide la ordenación de alertas sobre los países inicialmente inactivos; no es una precisión probabilística ni una validación temporal prospectiva. Apenas se registran cuatro entradas positivas por año. La clasificación de riesgo puede ser útil incluso si las probabilidades están sobreestimadas, pero estos dos años no bastan para certificarlo.</p>','soft')+
 box('<details><summary>Hipótesis nueva, trazabilidad y limitaciones</summary>'+
 '<p>'+safe(x.note)+'</p>'+
 '<p>La referencia específica usa 5.175 pares históricos iniciales para 2024 y 5.339 para 2025. Ambos casos se extraen de la edición original disponible en la reconstrucción, sin incorporar años de resultado a la estimación.</p>'+
 '<p><a href="./data/forecast-2027-entry-comparison.json" target="_blank" rel="noopener noreferrer">Ver todas las métricas, intervalos y presupuestos de alerta</a> · <a href="./data/forecast-2027-origin-state-diagnostic.json" target="_blank" rel="noopener noreferrer">Ver persistencia frente a entrada</a>.</p>'+
 '<p><strong>Estado</strong>: estudio retrospectivo exploratorio (post hoc), 0 resultados 2027 evaluados y las 196 probabilidades emitidas sin modificar.</p>'+
 '</details>','soft');
}
function renderOriginStateSkill(){
 const x=state.research?.origin_state_diagnostic_2027;
 if(!x)return "";
 const pct=n=>new Intl.NumberFormat("es-ES",{style:"percent",minimumFractionDigits:1,maximumFractionDigits:2}).format(n);
 const num=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:5,maximumFractionDigits:5}).format(n);
 const low=x.prior_below_threshold,high=x.prior_above_threshold;
 const labels=[["Por debajo del umbral en origen",low],["Ya por encima del umbral en origen",high]];
 return section("INVESTIGACIÓN · ORIGEN DEL PODER PREDICTIVO",
  "¿Detecta nuevas entradas o principalmente la persistencia?",
  "Dos años evaluados entre ediciones UCDP originales. Estado en el año de origen frente al estado dos años calendario después; NO mide el inicio de una guerra.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">UMBRAL YA SUPERADO</div><div class="card-number">'+safe(x.persisted_threshold_positives)+'</div><p>De '+safe(x.positive_threshold_years)+' positivos evaluados ('+pct(x.persisted_fraction_of_positives)+') son persistencia</p>')+
 box('<div class="eyebrow">NUEVOS CRUCES DEL UMBRAL</div><div class="card-number">'+safe(x.new_threshold_entries)+'</div><p>Solo ocho casos positivos partían por debajo de 25 muertes</p>')+
 box('<div class="eyebrow">PREDICCIONES 2027 EVALUADAS</div><div class="card-number">0</div><p>Las 196 probabilidades originales permanecen inalteradas</p>')+
 '</div>'+
 box('<h3>Comparación por estado inicial (Brier, menor es mejor)</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Estado en origen</th><th>Países-año</th><th>Positivos</th><th>Modelo por país</th><th>Markov global</th><th>Mejora Brier</th></tr></thead><tbody>'+
 labels.map(([name,g])=>'<tr><td>'+safe(name)+'</td><td>'+safe(g.n)+'</td><td>'+safe(g.events)+'</td><td>'+num(g.brier_model)+'</td><td>'+num(g.brier_global_markov)+'</td><td>'+pct(g.brier_skill_model_vs_markov)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Para países inicialmente por debajo del umbral, el intervalo exploratorio de diferencia Brier modelo − Markov global abarca ['+
 num(low.bootstrap_delta_brier_95pct[0])+', +'+num(low.bootstrap_delta_brier_95pct[1])+'] e <strong>incluye cero</strong>. No se ha demostrado una mejora fiable al detectar cruces nuevos. En el grupo ya activo, el intervalo es ['+
 num(high.bootstrap_delta_brier_95pct[0])+', '+num(high.bootstrap_delta_brier_95pct[1])+']. Ambos se basan solo en dos años objetivo.</p>','soft')+
 box('<h3>Transiciones observadas: de 2022 a 2024 y de 2023 a 2025</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Año evaluado</th><th>Por debajo → por encima</th><th>Por encima → por encima</th><th>Por encima → por debajo</th><th>Por debajo → por debajo</th></tr></thead><tbody>'+
 x.annual.map(a=>'<tr><td>'+safe(a.year)+'</td><td>'+safe(a.inactive_to_active)+'</td><td>'+safe(a.active_to_active)+'</td><td>'+safe(a.active_to_inactive)+'</td><td>'+safe(a.inactive_to_inactive)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Las alertas top-10 del modelo identificaron '+safe(x.annual[0].model_top_10_hits)+'/10 positivos en 2024 y '+safe(x.annual[1].model_top_10_hits)+'/10 en 2025. Sin embargo, este ranking está dominado por situaciones persistentes: <strong>no demuestra detección de nuevas guerras</strong>.</p>','soft')+
 box('<details><summary>Limitaciones y expediente reproducible</summary>'+
 '<p>'+safe(x.note)+'</p>'+
 '<p>Un horizonte de dos pasos de calendario desde el último año observado no equivale a dos años reales de preaviso desde la publicación de los datos. Los archivos históricos fueron recuperados y el cálculo se realizó ex post en 2026.</p>'+
 '<p><a href="./data/forecast-2027-origin-state-diagnostic.json" target="_blank" rel="noopener noreferrer">Ver informe íntegro por estado inicial, año y presupuesto de alertas</a>. Solo se publican agregados de la misma fuente UCDP institucional.</p>'+
 '</details>','soft');
}
function renderArchivalCrossRelease(){
 const r=state.research?.historical_cross_release_statebased;
 if(!r)return "";
 const n=v=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:5,maximumFractionDigits:5}).format(v);
 const pct=v=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2}).format(v*100)+" %";
 const method=[
   ["Markov por país",r.model_brier,r.model_logloss],
   ["Markov global",r.global_markov_brier,r.global_markov_logloss],
   ["Frecuencia global · 5 años",r.global_5y_brier,r.global_5y_logloss]
 ];
 return section("EVIDENCIA · EDICIONES OFICIALES DIFERENTES · UCDP",
    "¿Resiste el modelo las revisiones históricas de UCDP?",
    "Dos pruebas con entrenamiento de una edición antigua y resultados de otra posterior; mismo umbral y horizonte de dos años que GEO-2027. Reconstrucción ex post, no predicciones realmente emitidas en 2023/2024.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">OBSERVACIONES EXTERNAS</div><div class="card-number">'+safe(r.sample_size)+'</div><p>'+safe(r.events)+' países-año por encima del umbral, en 2024 y 2025</p>')+
 box('<div class="eyebrow">SKILL BRIER VS MARKOV GLOBAL</div><div class="card-number">'+pct(r.brier_skill_vs_markov)+'</div><p>Reducción retrospectiva de error; no resultado prospectivo certificado</p>')+
 box('<div class="eyebrow">EDICIONES INDEPENDIENTES</div><div class="card-number">4</div><p>23.1 y 24.1 para entrenamiento; 25.1 y 26.1 para resultados</p>')+
 '</div>'+
 box('<h3>Resultados agregados con auténticas ediciones históricas</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Brier ↓</th><th>Log-loss ↓</th></tr></thead><tbody>'+
 method.map(([name,brier,ll])=>'<tr><td>'+safe(name)+'</td><td>'+n(brier)+'</td><td>'+n(ll)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>El modelo por país mejora el Brier un '+pct(r.brier_skill_vs_markov)+' frente a Markov global y un '+
 pct(r.brier_skill_vs_global_5y)+' frente a la tasa global en esta muestra retrospectiva. El intervalo de bootstrap exploratorio por país para la diferencia Brier modelo − Markov global es ['+
 n(r.bootstrap95_delta_brier_markov[0])+', '+n(r.bootstrap95_delta_brier_markov[1])+']. No capta choques comunes de ambos años.</p>','soft')+
 box('<h3>Origen histórico, resultado y revisiones de etiquetas</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Origen</th><th>Resultado</th><th>Países-año</th><th>Con umbral</th><th>Brier país</th><th>Brier Markov global</th></tr></thead><tbody>'+
 r.folds.map(f=>'<tr><td>UCDP '+safe(f.origin)+' · '+safe(f.cutoff)+'</td><td>UCDP '+safe(f.assessment)+' · '+safe(f.year)+'</td><td>'+safe(f.observations)+'</td><td>'+safe(f.events)+'</td><td>'+n(f.model_brier)+'</td><td>'+n(f.global_markov_brier)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Al comparar las etiquetas previas al corte de cada edición, se observan '+
 r.historical_revisions.map(x=>safe(x.label_flips)+' cambios entre '+safe(x.origin)+' y '+safe(x.assessment)).join(' y ')+
 '. Las probabilidades se ajustaron con la versión antigua, sin incorporar esas revisiones futuras.</p>','soft')+
 box('<h3>Calibración retrospectiva entre ediciones</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Probabilidad estimada en retrospectiva</th><th>Países-año</th><th>Predicción media</th><th>Frecuencia observada</th></tr></thead><tbody>'+
 r.model_calibration_bins.map(x=>'<tr><td>'+pct(x.lower)+'–'+pct(x.upper)+'</td><td>'+safe(x.n)+'</td><td>'+(x.predicted===null?'—':pct(x.predicted))+'</td><td>'+(x.observed===null?'—':pct(x.observed))+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Error de calibración descriptivo por bandas: '+pct(r.model_bin_ece)+'. Algunas bandas contienen muy pocos países-año, por lo que no debe interpretarse como calibración prospectiva certificada.</p>','soft')+
 box('<details><summary>Fuentes oficiales, huellas y alcance científico</summary>'+
 Object.entries(r.source_releases).map(([version,source])=>
 '<p><a href="'+safe(source.url)+'" target="_blank" rel="noopener noreferrer">UCDP OrganizedViolenceCY '+safe(version)+'</a> · '+safe(source.rows)+' país-año hasta '+safe(source.last_year)+' · SHA-256 <code>'+safe(source.sha256)+'</code></p>').join("")+
 '<p>'+safe(r.caution)+'</p>'+
 '<p><a href="./data/forecast-2027-archival-cross-release.json" target="_blank" rel="noopener noreferrer">Examinar el experimento completo y las incertidumbres</a></p>'+
 '<p><strong>Estado GEO-2027:</strong> 196 pronósticos emitidos, cero desenlaces de 2027 resueltos. No se han alterado las probabilidades ni el protocolo original.</p>'+
 '</details>','soft');
}
function renderStatebasedHistoricalBacktest(){
 const e=state.research?.statebased_2027_spec_backtest;
 if(!e)return "";
 const n=value=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:5,minimumFractionDigits:5}).format(value);
 const pct=value=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2,minimumFractionDigits:2}).format(value*100)+" %";
 const models=[
   ["Markov por país",e.primary_brier_model,e.logloss_model],
   ["Markov global",e.secondary_brier_global_markov,e.logloss_global_markov],
   ["Frecuencia global · 5 años",e.primary_brier_global_5y,e.logloss_global_5y]
 ];
 return section("INVESTIGACIÓN · RETROSPECTIVA HISTÓRICA · UCDP 26.1",
   "El modelo emitido para 2027, probado con resultados históricos",
   "Reproducción del mismo modelo de horizonte dos años sobre 2012–2025. Fuentes históricas tomadas de una única edición revisada en 2026: no constituye un pronóstico emitido en aquellos años.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">AÑOS OBJETIVO</div><div class="card-number">'+safe(e.years.length)+'</div><p>2012–2025; entrenamiento separado dos años del objetivo</p>')+
 box('<div class="eyebrow">PAÍSES-AÑO OBSERVADOS</div><div class="card-number">'+safe(e.cohort_observations)+'</div><p>'+safe(e.country_year_positive)+' con al menos 25 muertes registradas</p>')+
 box('<div class="eyebrow">BRIER SKILL VS MARKOV GLOBAL</div><div class="card-number">'+pct(e.brier_skill_vs_global_markov)+'</div><p>Ventaja retrospectiva; sin demostración prospectiva</p>')+
 '</div>'+
 box('<h3>Comparación de errores de los tres modelos</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Brier ↓</th><th>Log-loss ↓</th></tr></thead><tbody>'+
 models.map(([label,brier,ll])=>'<tr><td>'+safe(label)+'</td><td>'+n(brier)+'</td><td>'+n(ll)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>El Markov por país mejora un '+pct(e.brier_skill_vs_global_5y)+' respecto a frecuencia global y un '+pct(e.brier_skill_vs_global_markov)+' respecto a Markov global en esta muestra <strong>retrospectiva</strong>. Brier y log-loss son menores; las probabilidades de 2027 no se han modificado.</p>'+
 '<p>Intervalo exploratorio de la diferencia Brier modelo − Markov global, remuestreando por país: ['+
 n(e.exploratory_country_cluster_ci_vs_markov[0])+', '+n(e.exploratory_country_cluster_ci_vs_markov[1])+
 ']. No capta choques comunes entre países ni toda la dependencia temporal.</p>','soft')+
 box('<h3>Calibración histórica: probabilidad media frente a frecuencia observada</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Rango</th><th>Registros</th><th>Predicción media</th><th>Frecuencia observada</th></tr></thead><tbody>'+
 e.reliability_bins.map(v=>'<tr><td>'+pct(v.lower)+'–'+pct(v.upper)+'</td><td>'+safe(v.n)+'</td><td>'+(v.predicted===null?'—':pct(v.predicted))+'</td><td>'+(v.observed===null?'—':pct(v.observed))+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Error de calibración agrupado descriptivo: '+pct(e.model_expected_calibration_error_bins)+
 ' para el modelo por país y '+pct(e.global_markov_expected_calibration_error_bins)+
 ' para Markov global. Estas diferencias dependen de los intervalos de agrupación y del archivo revisado.</p>','soft')+
 box('<details><summary>Los 14 años, fuentes y limitaciones</summary>'+
 '<div class="table-wrap"><table><thead><tr><th>Año</th><th>Países</th><th>Con el umbral</th><th>Brier país</th><th>Brier Markov global</th></tr></thead><tbody>'+
 e.annual_results.map(v=>'<tr><td>'+safe(v.year)+'</td><td>'+safe(v.n)+'</td><td>'+safe(v.positives)+'</td><td>'+n(v.model_brier)+'</td><td>'+n(v.global_markov_brier)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>'+safe(e.caution)+'</p>'+
 '<p><a href="./data/forecast-2027-historical-backtest.json" target="_blank" rel="noopener noreferrer">Descargar resultados agregados reproducibles</a> · <a href="'+safe(e.source_url)+'" target="_blank" rel="noopener noreferrer">Fuente oficial UCDP 26.1</a></p>'+
 '<p>SHA-256 de entrada <code>'+safe(e.source_sha256)+'</code>. No se han registrado resultados de 2027; la evaluación futura utilizará exclusivamente las 196 probabilidades ya publicadas.</p></details>','soft');
}
function renderRecencySensitivity(){
 const r=state.research?.recency_sensitivity_study;
 if(!r)return "";
 const inside=r.internally_revised_vintage, outside=r.cross_release_holdout_2024;
 const number=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:6,maximumFractionDigits:6}).format(n);
 const names=[["global_full","Global · histórico completo"],
  ["global_20","Global · 20 años"],["global_10","Global · 10 años"],["global_5","Global · 5 años"],
  ["country_full","Por país · histórico completo"],["country_20","Por país · 20 años"],
  ["country_10","Por país · 10 años"],["country_5","Por país · 5 años"]];
 return section("INVESTIGACIÓN · HIPÓTESIS DE RECENCIA · UCDP","¿Ayuda utilizar una frecuencia reciente de conflictos?",
  "Comparación de 5, 10 y 20 años frente al histórico completo, utilizando ediciones UCDP con la misma unidad de país-año. Exploración diseñada después de los primeros resultados, NO validación prospectiva.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">RETROSPECTIVA INTERNA · 2015–2022</div><div class="card-number">'+safe(inside.n)+'</div><p>'+safe(inside.events)+' eventos. Datos revisados de la misma edición.</p>')+
 box('<div class="eyebrow">CONTRASTE 2024 · EDICIÓN POSTERIOR</div><div class="card-number">'+safe(outside.n)+'</div><p>'+safe(outside.events)+' evento. Etiqueta de 25.1; resultado conocido anteriormente.</p>')+
 box('<div class="eyebrow">NUEVAS EMISIONES PROSPECTIVAS</div><div class="card-number">0</div><p>No se ha certificado una predicción anterior al desenlace.</p>')+
 '</div>'+
 box('<h3>Cuadrícula completa de ocho modelos (sin seleccionar ganador)</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Referencia</th><th>Brier 2015–2022 ↓</th><th>Brier 2024 ↓</th><th>Log-loss 2024 ↓</th></tr></thead><tbody>'+
 names.map(([key,name])=>'<tr><td>'+safe(name)+'</td><td>'+number(inside.pooled_metrics[key].brier)+'</td><td>'+number(outside.metrics[key].brier)+'</td><td>'+number(outside.metrics[key].logloss)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p><strong>Resultado:</strong> el baseline global de 5 años reduce ligeramente el Brier de 2024 respecto al global completo ('+
 number(outside.metrics.global_5.brier)+' frente a '+number(outside.metrics.global_full.brier)+
 '), pero el predictor por país continúa peor en Brier. Solo hay un positivo en 2024: las diferencias no demuestran superioridad estable.</p>'+
 '<details><summary>Procedencia, cobertura y limitaciones científicas</summary>'+
 '<p>'+safe(r.caveat)+'</p>'+
 '<p>Probabilidades históricas globales de entrenamiento: 5 años '+number(outside.training_rates["5"])+
 ', 10 años '+number(outside.training_rates["10"])+', 20 años '+number(outside.training_rates["20"])+
 ', histórico completo '+number(outside.training_full_global_rate)+'. Son frecuencias anteriores al año 2024, no probabilidades de alerta certificadas.</p>'+
 Object.entries(r.source_urls).map(([version,url])=>'<p><a href="'+safe(url)+'" target="_blank" rel="noopener noreferrer">UCDP '+safe(version)+'</a> · SHA-256 <code>'+safe(r.source_sha256[version])+'</code></p>').join("")+
 '<p>Protocolo, código y pruebas reproducibles en la cuenta institucional IDEA LAB. No se publican predicciones nacionales individuales.</p>'+
 '</details>','soft');
}
function renderExternalVintageHoldout(){
 const e=state.research?.external_vintage_holdout;
 if(!e)return "";
 const a=e.aggregate;
 const six=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:6,maximumFractionDigits:6}).format(n);
 const pct=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2}).format(n*100)+" %";
 const periods=e.studies.flatMap(s=>s.years);
 return section("INVESTIGACIÓN · ARCHIVO METODOLÓGICO · COMPARABILIDAD NO ACREDITADA",
   "Contraste mixto anterior: 715 observaciones, interpretación limitada",
   "Estudio exploratorio entre archivos históricos con posibles unidades de análisis diferentes. El fichero antiguo incluye varias entradas por país-año, a diferencia del formato posterior. No se emitieron predicciones en esos años.")+
 '<div class="notice alert"><strong>Advertencia de revisión científica:</strong> el resultado de −8,94 % en Brier NO constituye un backtest homogéneo validado. La agregación OR de duplicados del fichero 19.1 puede alterar la definición del evento. Conservamos las cifras para trazabilidad, no para compararlas directamente con el nuevo experimento de unidades homogéneas.</div>'+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">PAÍSES-AÑO EVALUADOS</div><div class="card-number">'+safe(a.country_years)+'</div><p>'+safe(a.events)+' comienzos de conflicto observados</p>')+
 box('<div class="eyebrow">MEJORA BRIER DEL MODELO</div><div class="card-number">'+safe(pct(a.relative_brier_skill_global))+'</div><p>Un valor negativo: el modelo por país empeora frente al global</p>')+
 box('<div class="eyebrow">VALIDEZ DE LA PREDICCIÓN</div><div class="card-number">No acreditada</div><p>Estudio ex post; ediciones y disponibilidad histórica imperfectas</p>')+
 '</div>'+
 box('<h3>Comparación externa de pérdidas probabilísticas</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Modelo</th><th>Brier ↓</th><th>Log-loss ↓</th></tr></thead><tbody>'+
 '<tr><td>País regularizado (prior 20)</td><td>'+six(a.brier_model)+'</td><td>'+six(a.logloss_model)+'</td></tr>'+
 '<tr><td>Frecuencia global</td><td>'+six(a.brier_global)+'</td><td>'+six(a.logloss_global)+'</td></tr>'+
 '<tr><td>Siempre sin conflicto (p=0)</td><td>'+six(a.brier_no_event)+'</td><td>No se presenta: p=0 asigna pérdida infinita si hay eventos</td></tr>'+
 '</tbody></table></div>'+
 '<p>El modelo por país tiene peor Brier y peor log-loss que la frecuencia global. El intervalo de bootstrap exploratorio (países, 2.000 réplicas) para la diferencia Brier país − global está entre '+six(a.cluster_bootstrap.global.delta_brier_95pct_interval[0])+' y '+six(a.cluster_bootstrap.global.delta_brier_95pct_interval[1])+'. No es una validación confirmatoria.</p>'+
 '<details><summary>Desglose anual y método</summary>'+
 '<div class="table-wrap"><table><thead><tr><th>Año</th><th>Países</th><th>Eventos</th><th>Brier país</th><th>Brier global</th></tr></thead><tbody>'+
 periods.map(p=>'<tr><td>'+safe(p.year)+'</td><td>'+safe(p.n)+'</td><td>'+safe(p.events)+'</td><td>'+six(p.brier_model)+'</td><td>'+six(p.brier_global)+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>Edición catalogada como 19.1: el CSV oficial enlazado acaba en 2017, aunque el codebook menciona 2018. Contiene '+safe(e.legacy_19_1_duplicates.duplicate_country_year_keys)+' claves país-año repetidas; '+safe(e.legacy_19_1_duplicates.contradictory_onset2_keys)+' con etiqueta incompatible. Se utilizó una agregación OR exploratoria y otra sensibilidad eliminando esos casos. En esta última el Brier Skill frente al global es '+safe(pct(e.legacy_duplicate_exclusion_sensitivity.relative_brier_skill_global))+'.</p>'+
 '<p>'+safe(e.explanatory_note)+'</p>'+
 Object.entries(e.sources).map(([version,item])=>'<p><a href="'+safe(item.url)+'" target="_blank" rel="noopener noreferrer">UCDP '+safe(version)+'</a> · SHA-256 <code>'+safe(item.sha256)+'</code></p>').join("")+
 '<p>Expediente reproducible en GitHub Actions #'+safe(e.workflow_run)+'. Fuentes oficiales abiertas; solo se publica el agregado, no pronósticos nacionales ni archivos privados.</p>'+
 '</details>','soft');
}
function renderVintageHoldout(){
 const r=state.research?.historical_vintage_2024;
 if(!r)return "";
 const number=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:6,maximumFractionDigits:6}).format(n);
 const improvement=new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(r.relative_brier_skill*100)+" %";
 const loglossGain=new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(100*(1-r.logloss_model/r.logloss_global))+" %";
 return section("INVESTIGACIÓN · VALIDACIÓN ENTRE EDICIONES · UCDP","¿Qué ocurre cuando no entrenamos con datos revisados del futuro?",
  "Contraste para 2024 con datos UCDP 23.1, publicados como edición de 2023. La etiqueta del resultado procede de UCDP 25.1. Se calculó retrospectivamente, no se emitió ninguna predicción en 2024.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">PAÍSES ANALIZADOS</div><div class="card-number">'+safe(r.sample_size)+'</div><p>'+safe(r.positives)+' inicio/reanudación observado</p>')+
 box('<div class="eyebrow">MEJORA BRIER</div><div class="card-number">'+safe(improvement)+'</div><p>Valor negativo: el modelo por país empeora respecto al global.</p>')+
 box('<div class="eyebrow">VALIDEZ</div><div class="card-number">No concluyente</div><p>Un solo episodio; no hay prueba de capacidad anticipatoria.</p>')+
 '</div>'+
 box('<h3>Comparación sin variables posteriores a 2022</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Referencia</th><th>Brier ↓</th><th>Log-loss ↓</th></tr></thead><tbody>'+
 '<tr><td>Frecuencia histórica global</td><td>'+safe(number(r.brier_global))+'</td><td>'+safe(number(r.logloss_global))+'</td></tr>'+
 '<tr><td>Modelo histórico por país</td><td>'+safe(number(r.brier_model))+'</td><td>'+safe(number(r.logloss_model))+'</td></tr>'+
 '</tbody></table></div>'+
 '<p><strong>Resultado:</strong> '+safe(r.conclusion)+'</p>'+
 '<p><strong>Discrepancia de pérdidas:</strong> Brier empeora, mientras log-loss mejora '+safe(loglossGain)+' frente a la frecuencia histórica global. Son métricas diferentes y seleccionar después la favorable no demuestra capacidad predictiva. Un solo positivo impide valorar calibración o utilidad operativa con fiabilidad.</p>'+
 '<p>El intervalo exploratorio de la diferencia Brier país − global incluye cero: ['+safe(number(r.uncertainty_brier_delta[0]))+', '+safe(number(r.uncertainty_brier_delta[1]))+']. Por su diseño y número de eventos no permite declarar superioridad ni inferioridad estable.</p>'+
 '<details><summary>Cómo se verificaron las versiones y qué falta</summary>'+
 '<p>'+safe(r.caveat)+'</p>'+
 r.sources.map((src,i)=>'<p><a href="'+safe(src.url)+'" target="_blank" rel="noopener noreferrer">Edición UCDP '+(i===2?'25.1':'23.1')+' · fuente '+(i+1)+'</a> · SHA-256 <code>'+safe(src.sha256)+'</code></p>').join("")+
 '<p>La validación reproducible y los tests están disponibles en el estudio institucional privado; el archivo público solo contiene agregados oficiales, sin datos del laboratorio personal.</p>'+
 '</details>','soft');
}
function renderConditionalRisksetEvidence(){
 const study=state.research?.riskset_study;
 if(!study)return "";
 const fmt=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:6,minimumFractionDigits:6}).format(n);
 const percent=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(100*n)+" %";
 const first=study.scenarios[0],second=study.scenarios[1];
 return section("INVESTIGACIÓN · UCDP · SEGUNDO EXPERIMENTO","¿Importa que un país ya esté en guerra?",
   "Hemos cruzado inicios de conflictos con la incidencia previa: el análisis distingue países sin violencia intrastatal activa durante uno o dos años anteriores.")+
 '<div class="section-grid three">'+
 box('<div class="eyebrow">SIN CONFLICTO EN EL AÑO PREVIO</div><div class="card-number">'+safe(percent(first.relative_brier_improvement))+'</div><p>Menor error Brier que la frecuencia global · '+safe(first.observations)+' países-año</p>')+
 box('<div class="eyebrow">SIN CONFLICTO EN DOS AÑOS</div><div class="card-number">'+safe(percent(second.relative_brier_improvement))+'</div><p>Menor error Brier que la frecuencia global · '+safe(second.observations)+' países-año</p>')+
 box('<div class="eyebrow">AVISO DE VALIDEZ</div><div class="card-number">Exploratorio</div><p>Sin emisión prospectiva ni vintages históricas verificadas</p>')+
 '</div>'+
 box('<h3>Comparativa del modelo por país frente a la referencia global</h3>'+
 '<div class="table-wrap"><table><thead><tr><th>Países sin conflicto en...</th><th>Países</th><th>Eventos</th><th>Brier país ↓</th><th>Brier global ↓</th><th>Mejora relativa</th></tr></thead><tbody>'+
 study.scenarios.map(v=>'<tr><td>'+safe(v.preceding_inactive_years)+' año'+(v.preceding_inactive_years>1?'s':'')+
 '</td><td>'+safe(v.countries)+'</td><td>'+safe(v.events)+'</td><td>'+safe(fmt(v.brier_model))+
 '</td><td>'+safe(fmt(v.brier_baseline))+'</td><td>'+safe(percent(v.relative_brier_improvement))+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p><strong>Lectura:</strong> las dos comparaciones favorecen al modelo por país dentro de estas muestras. Los intervalos exploratorios excluyen cero, pero no están corregidos por seleccionar criterios tras mirar el primer experimento. Esto <strong>no acredita predicción futura</strong>.</p>'+
 '<details><summary>¿Es estable el resultado entre periodos?</summary>'+
 '<div class="table-wrap"><table><thead><tr><th>Inactividad previa</th><th>Periodo</th><th>Eventos</th><th>Mejora Brier</th></tr></thead><tbody>'+
 study.temporal_robustness.periods.map(v=>'<tr><td>'+safe(v.prior_inactive_years)+' año(s)</td><td>'+safe(v.years)+
 '</td><td>'+safe(v.events)+'</td><td>'+safe(percent(v.relative_brier_improvement))+'</td></tr>').join("")+
 '</tbody></table></div>'+
 '<p>El análisis también compara tres niveles de regularización: '+study.temporal_robustness.priors.map(v=>safe(v.prior_inactive_years)+' año(s) · prior '+safe(v.prior_strength)+': '+safe(percent(v.relative_brier_improvement))).join(' · ')+'.</p>'+
 '<p>'+safe(study.temporal_robustness.note)+'</p>'+
 '</details>'+
 '<details><summary>Fuentes oficiales, intervalos y limitaciones</summary>'+
 '<p><strong>Periodo:</strong> '+safe(study.period)+' · 40 eventos en cada muestra.</p>'+
 study.scenarios.map(v=>'<p>Sin conflicto en '+safe(v.preceding_inactive_years)+' año(s), delta Brier país − global, intervalo exploratorio 95 %: ['+safe(fmt(v.cluster_delta_interval[0]))+', '+safe(fmt(v.cluster_delta_interval[1]))+'].</p>').join("")+
 study.sources.map((src,i)=>'<p><a href="'+safe(src.url)+'" target="_blank" rel="noopener noreferrer">Fuente oficial '+(i+1)+'</a> · SHA-256 <code>'+safe(src.sha256)+'</code></p>').join("")+
 '<p>'+safe(study.note)+'</p>'+
 '</details>','soft');
}
function renderEmpiricalEvidence(){
 const study=state.research?.empirical_studies?.[0];
 if(!study)return "";
 const six=n=>new Intl.NumberFormat("es-ES",{minimumFractionDigits:6,maximumFractionDigits:6}).format(n);
 const p=n=>new Intl.NumberFormat("es-ES",{maximumFractionDigits:2}).format(n*100)+" %";
 const ci=study.delta_brier_confidence_interval;
 return section("INVESTIGACIÓN · UCDP · RESULTADOS REALES","Primer contraste retrospectivo",
   "Resultados calculados sobre el dataset oficial, no una simulación. La edición UCDP 25.1 fue revisada después de los años evaluados: NO es una prueba prospectiva ni una reconstrucción point-in-time.")+
 '<div class="section-grid three">'+
  box('<span class="tiny">OBSERVACIONES PAÍS-AÑO</span><div class="card-number">'+safe(study.observations)+'</div><p>'+safe(study.countries)+' países; '+safe(study.positive_events)+' inicios/reanudaciones</p>')+
  box('<span class="tiny">BRIER POR PAÍS</span><div class="card-number">'+safe(six(study.brier_country))+'</div><p>Modelo suavizado con historia específica de país</p>')+
  box('<span class="tiny">BRIER GLOBAL</span><div class="card-number">'+safe(six(study.brier_global))+'</div><p>Referencia simple obligatoria</p>')+
 '</div>'+
 box('<h3>¿Mejora la predicción respecto a la tasa base?</h3>'+
  '<p><strong>Mejora numérica Brier: '+safe(p(study.relative_brier_improvement))+'</strong>. Es pequeña y no demuestra una ventaja estable.</p>'+
  '<p>Intervalo exploratorio del cambio de error (país − global): <strong>['+safe(six(ci[0]))+', '+safe(six(ci[1]))+']</strong>. Incluye cero; <strong>no hay superioridad robusta demostrada</strong>.</p>'+
  '<div class="table-wrap"><table><thead><tr><th>Referencia</th><th>Brier ↓</th></tr></thead><tbody>'+
  '<tr><td>Frecuencia histórica por país (suavizada)</td><td>'+safe(six(study.brier_country))+'</td></tr>'+
  '<tr><td>Frecuencia histórica global</td><td>'+safe(six(study.brier_global))+'</td></tr>'+
  '<tr><td>Siempre sin inicio</td><td>'+safe(six(study.brier_no_event))+'</td></tr>'+
  '</tbody></table></div>'+
  '<details><summary>Fuente, reproducibilidad y limitaciones</summary>'+
  '<p><strong>Periodo:</strong> '+safe(study.period)+' · '+safe(study.data_version)+'</p>'+
  '<p><strong>Fuente oficial:</strong> <a href="'+safe(study.source_url)+'" target="_blank" rel="noopener noreferrer">UCDP Onset 25.1 (CC BY 4.0)</a></p>'+
  '<p><strong>SHA-256:</strong> <code>'+safe(study.source_sha256)+'</code></p>'+
  '<p>'+safe(study.note)+'</p>'+
  '</details>','soft');
}
function renderScience(){
 const d=state.data,rows=d.studies.map(s=>({s,score:score(s)}));
 return renderNewEntryComparator()+renderOriginStateSkill()+renderArchivalCrossRelease()+renderStatebasedHistoricalBacktest()+renderRecencySensitivity()+renderExternalVintageHoldout()+renderVintageHoldout()+renderHistoricalLabelRevisions()+renderConditionalRisksetEvidence()+renderEmpiricalEvidence()+section("INVESTIGACIÓN · DEMOSTRACIONES","Pruebas sintéticas del evaluador","La tabla siguiente usa muestras inventadas para probar el software; no debe confundirse con el contraste UCDP real mostrado arriba.")+
 '<div class="table-wrap"><table><thead><tr><th>Estudio sintético</th><th>Observaciones</th><th>Brier modelo</th><th>Brier referencia</th><th>Mejora relativa</th><th>Validez</th></tr></thead><tbody>'+rows.map(({s,score:r})=>'<tr><td>'+safe(s.title)+'</td><td>'+r.n+'</td><td>'+format(r.brier)+'</td><td>'+format(r.baselineBrier)+'</td><td>'+formatPct(r.skill)+'</td><td>Sintético</td></tr>').join("")+'</tbody></table></div>'+
 section("REPRODUCIBILIDAD","Evaluación de un experimento","Selecciona un estudio para analizar las probabilidades ficticias y compararlas con su referencia fija.")+
 renderStudySelector()+'<div class="two-col">'+box('<svg id="study-chart" class="chart-svg frame-chart" viewBox="0 0 760 285" role="img" aria-label="Evaluación probabilística ficticia"></svg>')+
 box('<div class="tiny">CONTRASTE</div><div id="score-info"></div><p>La métrica de Brier mide el error cuadrático de probabilidades entre 0 y 1; valores menores indican menor error en este conjunto.</p>')+'</div>'+
 section("REGLAS DE ADMISIÓN","Separar evaluación retrospectiva y prospectiva","Los test revisados y las simulaciones no pueden presentarse como rendimientos reales de un sistema de anticipación.")+methods()+syntheticWarning();
}
function renderUsefulQuestions(){
 const d=state.research;
 if(!d)return section("INVESTIGACIÓN · AGENDA","Preguntas útiles","Registro temporalmente no disponible.")+
   msg("No se mostrarán hipótesis sin protocolo revisado.", "alert");
 const tiers=[["P1","Investigación prioritaria"],["P2","Siguientes experimentos"],["P3","Exploración a largo plazo"]];
 const visible=d.questions.filter(q=>q.priority===state.questionPriority);
 const names=Object.fromEntries(d.programs.map(p=>[p.id,p.title]));
 return section("INVESTIGACIÓN · UTILIDAD","¿Qué queremos anticipar?",
  "Priorizamos preguntas cuya respuesta podría cambiar una decisión, con un fenómeno verificable, horizonte y referencia. Prioridad no significa precisión demostrada.")+
  '<div class="button-group" role="group" aria-label="Prioridad de investigaciones">'+tiers.map(([tier,label])=>
   button(label+" · "+d.questions.filter(q=>q.priority===tier).length,"question-priority",tier,
    state.questionPriority===tier?"ghost active":"ghost")).join("")+'</div>'+
  '<p class="tiny" style="margin-top:12px">'+safe(d.priority_method)+'</p>'+
  '<div class="section-grid research-questions">'+visible.map((q,i)=>
   box('<div class="item-row wrap"><div class="eyebrow">'+safe(q.id)+' · '+safe(names[q.program])+
      '</div>'+tag(q.model_status==="retrospectivo_no_prospectivo"?"Árbol retrospectivo disponible":
      q.model_status==="fuente_pendiente"?"Fuente pendiente":"Modelo por desarrollar")+'</div>'+
    '<h3>'+(i+1)+'. '+safe(q.question)+'</h3>'+
    '<p><strong>¿Para qué serviría?</strong> '+safe(q.decision)+'</p>'+
    '<div class="grid-stats"><div><strong>'+safe(q.horizon)+'</strong><span>Horizonte</span></div>'+
    '<div><strong>Sin validar</strong><span>Capacidad predictiva</span></div></div>'+
    '<details><summary>Protocolo, datos y condición de validación</summary>'+
      '<p><strong>Desenlace observable:</strong> '+safe(q.target)+'</p>'+
      '<p><strong>Referencia mínima:</strong> '+safe(q.baseline)+'</p>'+
      '<p><strong>Fuente y límites:</strong> '+safe(q.source_note)+'</p>'+
      '<p><strong>Siguiente experimento:</strong> '+safe(q.gate)+'</p>'+
    '</details>'
   )).join("")+'</div>'+
   box('<h3>Cómo se demostrará utilidad</h3><p>Para cada pregunta registraremos una predicción antes del periodo objetivo, congelaremos las variables disponibles en esa fecha, compararemos contra una referencia simple y publicaremos los errores. Un resultado bonito en un árbol histórico no permite declarar que predice.</p>'+
      '<p>Evaluaremos Brier score y calibración para probabilidades; MAE/CRPS para cantidades; y la mejora de decisiones con una función de coste definida antes de conocer el resultado. Los eventos raros requieren especial atención a tasa base y falsos positivos.</p>',
      "soft");
}
function renderResearchRegistry(){
 const d=state.research;
 if(!d)return section("INVESTIGACIÓN","Líneas y fuentes","El registro independiente no está disponible.")+msg("Sin registro de fuentes verificado; no se muestran resultados de respaldo.","alert");
 const domains=["todos",...new Set(d.programs.map(p=>p.domain))];
 const filtered=state.registryFilter==="todos"?d.programs:d.programs.filter(p=>p.domain===state.registryFilter);
 const r=state.registryOutput;
 const report=r?box('<div class="section-grid three"><div><span class="tiny">OBSERVACIONES</span><h3>'+r.n+'</h3></div><div><span class="tiny">BRIER MODELO</span><h3>'+format(r.model_brier)+'</h3></div><div><span class="tiny">BRIER BASELINE</span><h3>'+format(r.baseline_brier)+'</h3></div></div><p>Mejora aritmética relativa: '+formatPct(r.relative_skill)+'. '+safe(r.notice)+'</p>'):'<p class="tiny">Sin observaciones evaluadas en esta sesión.</p>';
 return section("INVESTIGACIÓN · FUENTES","Siete líneas científicas","Preguntas contrastables y fuentes primarias. No son siete modelos validados ni siete predicciones emitidas.")+
 domainGraph(d.programs,state.registryFilter)+
  '<div class="button-group">'+domains.map(x=>button(x,"registry-filter",x,state.registryFilter===x?"ghost active":"ghost")).join("")+'</div>'+
 '<div class="table-wrap" style="margin-top:14px"><table><thead><tr><th>Línea</th><th>Objetivo observable</th><th>Situación</th><th>Fuente primaria</th></tr></thead><tbody>'+
 filtered.map(p=>'<tr><td><strong>'+safe(p.title)+'</strong><div class="tiny">'+safe(p.id)+' · '+safe(p.domain)+'</div><p>'+safe(p.question)+'</p></td><td>'+safe(p.outcome)+'<div class="tiny">Referencia: '+safe(p.baseline)+'</div></td><td>'+tag(p.stage)+'<div class="tiny" title="'+safe(p.next_gate)+'">'+safe(p.next_gate)+'</div></td><td><a href="'+safe(p.source.url)+'" target="_blank" rel="noopener noreferrer">'+safe(p.source.name)+'</a><div class="tiny">'+safe(p.public_evidence)+'</div></td></tr>').join("")+'</tbody></table></div>'+
 section("EVALUACIÓN · LOCAL","Evaluador probabilístico","Calcula Brier respecto a una referencia a partir de un archivo CSV en tu navegador. Las fechas escritas no acreditan por sí mismas su veracidad.")+
 box('<label class="field">CSV (máximo 500 KB y 2.000 filas)<input type="file" id="research-csv" accept=".csv,text/csv"></label><div class="button-group">'+button("Descargar ejemplo CSV","download-research-csv","")+'</div>'+report)+
 msg("Evaluación aritmética local, sin transferencia del archivo ni certificación externa de fuentes, fechas o desenlaces.");
}

function renderOperations(){
 const d=state.data;
 return section("INVESTIGACIÓN · TRAZABILIDAD","Registro público","Inventario de experimentos de muestra y de sus limitaciones. No se transfieren registros de trabajo ni referencias a bases de datos ajenas.")+
 '<div class="table-wrap"><table><thead><tr><th>ID de demostración</th><th>Objeto de estudio</th><th>Horizonte</th><th>Procedimiento</th><th>Estado</th></tr></thead><tbody>'+d.studies.map(s=>'<tr><td>'+safe(s.id)+'</td><td>'+safe(s.title)+'</td><td>'+safe(s.horizon)+'</td><td>'+safe(s.method)+'</td><td>'+tag("Ficticio")+'</td></tr>').join("")+'</tbody></table></div>'+
 box('<h3>Control de origen</h3><p>El registro público requiere para cada futuro experimento: identificador nuevo, instante de emisión, conjunto de datos y edición, algoritmo versionado, horizonte y resolución externa independiente.</p>'+
 msg("Este sitio ofrece exclusivamente contenidos públicos y ejemplos de carácter ilustrativo."),"soft")+
 section("CÓMO PUBLICAREMOS","Contrato para nuevas evaluaciones","No se aceptan entradas sin información suficiente para comprobar el orden temporal entre pronóstico, datos y resolución.")+methods();
}
function renderRoadmap(){
 const d=state.data;
 const ms=d.milestones.filter(m=>state.filter==="todos"||m.state===state.filter);
 const labels={verificado:"Verificado técnicamente",pendiente:"En preparación",bloqueado:"Bloqueado"};
 return section("INVESTIGACIÓN · SEGUIMIENTO","Hitos y criterios","Cada verificación técnica tiene su evidencia. Completar una interfaz o un test no implica haber demostrado capacidad predictiva.")+
 '<div class="button-group">'+[["todos","Todos"],["verificado","Verificados"],["pendiente","Pendientes"],["bloqueado","Bloqueados"]].map(([id,name])=>button(name,"filter",id,state.filter===id?"ghost active":"ghost")).join("")+'</div>'+
 '<div class="stack" style="margin-top:14px">'+ms.map(m=>box('<div class="item-row wrap"><div><span class="tiny">'+safe(m.id)+' · '+safe(m.group)+'</span><h3>'+safe(m.title)+'</h3></div>'+tag(labels[m.state]||m.state,m.state==="bloqueado"?"alert":"")+'</div><p>'+safe(m.evidence)+'</p>')).join("")+'</div>'+
 msg("Los estados de esta hoja de ruta describen únicamente la nueva aplicación pública y su demostración sintética.");
}
function renderIdeas(){
 const d=state.data,items=[...d.ideas,...state.ideas];
 const mapping=Object.fromEntries(d.programs.map(p=>[p.id,p.name]));
 return section("CREAR · INVESTIGACIÓN","Ideas y sinergias","Visualiza las relaciones entre preguntas de investigación y líneas metodológicas. Puedes redactar una idea de trabajo en esta sesión sin enviarla a ningún servidor.")+
 '<div class="section-grid three">'+items.map(x=>box('<div class="item-row wrap"><span class="tiny">'+safe(x.id)+'</span>'+tag(x.area)+'</div><h3>'+safe(x.title)+'</h3><p>'+safe(x.question)+'</p><div class="button-group">'+x.links.map(id=>tag(mapping[id]||id)).join("")+'</div>')).join("")+'</div>'+
 section("PROPONER","Crear una hipótesis local","Esta herramienta funciona únicamente en memoria. Si recargas la página, los borradores se descartan.")+
 '<form id="idea-form" class="panel" autocomplete="off"><div class="section-grid"><label class="field">Nombre de la hipótesis<input name="title" required maxlength="110" placeholder="Título contrastable"></label><label class="field">Línea de investigación<select name="program">'+d.programs.map(p=>'<option value="'+safe(p.id)+'">'+safe(p.name)+'</option>').join("")+'</select></label></div><label class="field">Pregunta falsable<textarea name="question" maxlength="600" required placeholder="¿Qué observación permitiría contrastarla?"></textarea></label><div class="form-actions"><button class="action primary" type="submit">Añadir a esta sesión</button>'+button("Exportar borradores JSON","export-ideas","","ghost")+'</div></form>'+
 msg("No se guardan borradores en GitHub, Drive, cookies ni bases de datos. La exportación es una descarga local iniciada por ti.");
}
function renderVideo(){
 const d=state.data;
 const selected=d.studies.find(x=>x.id===state.study)||d.studies[0];
 return section("CREAR · DIVULGACIÓN","Estudio audiovisual","Generador local de estructura narrativa para explicar hipótesis y limitaciones. No crea vídeos ni publica contenido por sí mismo.")+
 '<div class="two-col">'+box('<h3>Guion de investigación</h3>'+renderStudySelector()+'<div class="field">Enfoque narrativo<select id="video-style"><option value="cientifico">Rigor y método</option><option value="divulgativo">Divulgación general</option><option value="critico">Evaluación crítica</option></select></div>'+button("Preparar guion","make-video","","action primary")+
 '<p>El guion se produce en tu navegador a partir del estudio ficticio seleccionado.</p>')+
 box('<div class="video-frame"><div><div class="eyebrow">IDEA LAB · ESTUDIO AUDIOVISUAL</div><h3>'+safe(selected.title)+'</h3><p>Guion local · Sin generación de vídeo</p></div></div>')+'</div>'+
 box('<h3>Borrador narrativo</h3><textarea readonly id="video-output" aria-label="Guion audiovisual" style="min-height:195px">Elige un estudio y pulsa Preparar guion.</textarea><div class="form-actions">'+button("Copiar guion","copy-video","","ghost")+'</div><div class="tiny" id="copy-status"></div>')+
 msg("No se añaden voz, imagen, música, logos externos ni testimonios ficticios. Todo resultado debe señalar sus fuentes y su carácter experimental.");
}
function svgNode(name,attrs={},content){
 const elem=document.createElementNS("http://www.w3.org/2000/svg",name);
 Object.entries(attrs).forEach(([key,value])=>elem.setAttribute(key,String(value)));
 if(content!==undefined)elem.textContent=String(content);
 return elem;
}
function updateChart(){
 const svg=$("study-chart");if(!svg||!state.data)return;
 const s=state.data.studies.find(x=>x.id===state.study)||state.data.studies[0];
 svg.replaceChildren();
 const x=i=>55+i*125,y=v=>242-202*v;
 [0,.25,.5,.75,1].forEach(p=>{svg.append(svgNode("line",{x1:55,x2:710,y1:y(p),y2:y(p),stroke:"#344958","stroke-width":1}),svgNode("text",{x:4,y:y(p)+4,fill:"#8caabd","font-size":12},Math.round(p*100)+" %"));});
 svg.append(svgNode("line",{x1:55,x2:710,y1:y(s.baseline),y2:y(s.baseline),stroke:"#c8a16a","stroke-dasharray":"6 6","stroke-width":1.8}));
 const points=s.probabilities.map((p,i)=>x(i)+","+y(p)).join(" ");
 svg.append(svgNode("polyline",{points,stroke:"#82d5e8","stroke-width":2.9,fill:"none","stroke-linejoin":"round"}));
 s.probabilities.forEach((p,i)=>{svg.append(svgNode("circle",{cx:x(i),cy:y(p),r:5,fill:"#82d5e8"}),svgNode("circle",{cx:x(i),cy:y(s.outcomes[i]),r:5,stroke:"#071318","stroke-width":1.5,fill:"#87d8bd"}),svgNode("text",{x:x(i),y:269,"text-anchor":"middle","font-size":12,fill:"#91a7b7"},s.issued[i]));});
 const info=$("score-info");
 if(info){
 const r=score(s);
 info.innerHTML='<h3>'+safe(s.title)+'</h3><p>'+safe(s.question)+'</p><div class="grid-stats"><div><strong>'+format(r.brier)+'</strong><span>Brier sintético</span></div><div><strong>'+format(r.baselineBrier)+'</strong><span>Referencia</span></div><div><strong>'+formatPct(r.skill)+'</strong><span>Mejora ficticia</span></div></div>';
 }
}
let disposeScientificNeural=()=>{};
function render(){
 if(!state.data)return;
 disposeScientificNeural();disposeScientificNeural=()=>{};
 const group=viewToGroup[state.view];
 document.querySelectorAll("[data-section]").forEach(button=>{
  const active=button.dataset.section===group;button.classList.toggle("active",active);button.setAttribute("aria-pressed",String(active));
 });
 const sub=$("subtabs");sub.replaceChildren();sub.hidden=group==="brief";
 if(group!=="brief")for(const [id,label] of groupViews[group]){
  const b=document.createElement("button");b.type="button";b.textContent=label;b.dataset.action="navigate";b.dataset.value=id;
  b.classList.toggle("active",state.view===id);sub.append(b);
 }
 const views={archive:renderArchive,brief:()=>button("Ver estructura del archivo científico","navigate","archive")+renderBrief(),futures:renderFutures,shadow2027:renderShadow,overview:renderOverview,
  science:renderScience,questions:renderUsefulQuestions,registry:renderResearchRegistry,operations:renderOperations,roadmap:renderRoadmap,
  portfolio:()=>renderHistoricalProjectPortfolio(state.projectCatalog),ideas:renderIdeas,video:renderVideo};
 $("app").innerHTML=views[state.view]();
 updateChart();
 disposeScientificNeural=enableScientificNeural($("app"),state.data.programs,state.program);
}
function navigate(view){
 if(!viewIds.has(view))return;
 state.view=view;
 const url=new URL(location.href);url.searchParams.set("view",view);history.pushState({view},"",url);
 render();
 window.scrollTo({top:0,behavior:"auto"});
}
async function loadPublicTree(){
 try{
  const response=await fetch("./data/countries-ucdp261.json",{cache:"no-store"});
  if(!response.ok)throw Error("DATOS_UCDP_NO_DISPONIBLES");
  const text=await response.text();
  if(text.length>500000)throw Error("CATALOGO_UCDP_EXCESIVO");
  const records=JSON.parse(text);
  acceptPublicCountryCatalogs(records);
 }catch(error){
  setCountrySourceError("No se ha podido cargar el registro de países de UCDP. "+String(error.message));
 }
 if(state.view==="futures")render();
}
async function load(){
 if(state.busy)return;state.busy=true;$("refresh").disabled=true;$("sync-status").textContent="Validando el registro público…";
 try{
  const catalogRead=loadProjectCatalog().then(data=>({available:true,data}))
    .catch(()=>({available:false,data:null}));
  const [response,researchResponse,forecastResponse,manifestResponse]=await Promise.all([
     fetch("./data/demo.json",{cache:"no-store"}),
     fetch("./data/research.json",{cache:"no-store"}),
     fetch("./data/forecast-2027-ucdp261.json",{cache:"no-store"}),
     fetch("./data/forecast-2027-manifest.json",{cache:"no-store"})
   ]);
   if(!response.ok||!researchResponse.ok||!forecastResponse.ok||!manifestResponse.ok)
     throw new Error("Public sources unavailable");
   const [data,research,forecastText,manifest]=await Promise.all([
     response.json(),researchResponse.json(),forecastResponse.text(),manifestResponse.json()
   ]);
   if(!globalThis.crypto?.subtle)throw new Error("SHA-256 unavailable on this client");
   const bytes=new TextEncoder().encode(forecastText);
   const digest=await crypto.subtle.digest("SHA-256",bytes);
   const hash=Array.from(new Uint8Array(digest)).map(x=>x.toString(16).padStart(2,"0")).join("");
   if(hash!==manifest.forecast_sha256)throw new Error("Forecast content integrity failure");
   const prospective=JSON.parse(forecastText);
   verify(data);verifyResearch(research);verifyIssuedForecast2027(prospective,manifest);
   state.research=research;state.prospective2027=prospective;state.prospective2027Manifest=manifest;
  // Detailed scientific records are intentionally not read by the public client.
  state.projectCatalog=(await catalogRead).data;
  for(const key of ["programs","milestones","ideas"])if(!Array.isArray(data[key]))throw new Error("Incomplete public catalogue");
  state.data=data;state.scenario=state.scenario||data.branches[0].id;state.program=state.program||data.programs[0].id;state.study=state.study||data.studies[0].id;
  $("count-studies").textContent=data.studies.length;$("count-models").textContent=data.programs.length;
  $("count-predictions").textContent="1177";$("count-evaluated").textContent="0";
  $("as-of").textContent="1 cohorte GEO-2027 emitida · evaluación pendiente";
  $("sync-status").textContent="Emisión GEO-2027 pública y con SHA-256 verificado · 0 resultados resueltos";
  render();
  await loadPublicTree();
 }catch{
  $("sync-status").textContent="Fuente pública no disponible o inválida";
  if(!state.data)$("app").innerHTML=msg("No se ha podido cargar el registro público. No se muestran resultados de respaldo inventados.");
 }finally{state.busy=false;$("refresh").disabled=false;}
}
function makeVideo(){
 const s=state.data.studies.find(x=>x.id===state.study)||state.data.studies[0];
 const style=$("video-style")?.value||"cientifico";
 const opener=style==="divulgativo"?"¿Se puede anticipar este fenómeno?":
 style==="critico"?"¿Estamos confundiendo resultados de una simulación con una predicción?":
 "Una hipótesis es útil cuando admite un contraste independiente.";
 state.videoText=[
 "IDEA LAB · Guion de demostración (datos sintéticos)","",
 "INTRODUCCIÓN",""+opener,"Pregunta: "+s.question,"",
 "MÉTODO","Diseño: "+s.method,"Horizonte: "+s.horizon,"",
 "CONTRASTE","Mostrar la regla anterior a los datos y comparar con una referencia.",
 "Este ejemplo no utiliza observaciones reales y no demuestra capacidad predictiva.","",
 "LÍMITES",s.limits,"",
 "CIERRE","Antes de afirmar utilidad: datos point-in-time, evaluación fuera de muestra y resultados resueltos."
 ].join("\n");
 const out=$("video-output");if(out)out.value=state.videoText;
}
function exportIdeas(){
 const output={data_class:"local_draft",version:1,ideas:state.ideas};
 const url=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:"application/json"}));
 const link=document.createElement("a");link.href=url;link.download="borradores-investigacion.json";document.body.append(link);link.click();link.remove();
 URL.revokeObjectURL(url);
}
document.querySelectorAll("[data-section]").forEach(button=>button.addEventListener("click",()=>{
 const group=button.dataset.section;navigate(groupViews[group][0][0]);
}));
$("refresh").addEventListener("click",load);
// Country controls use the official UCDP-derived public tree, fetched automatically.
$("app").addEventListener("change",event=>{
 if(event.target?.id!=="geo2027-country")return;
 const id=Number(event.target.value);
 if(!state.prospective2027?.countries.some(x=>x.country_id===id))return;
 state.forecastCountryId=id;render();
});
$("app").addEventListener("change",event=>{
 const input=event.target;
 const key={
  "tree-country-origin":"countryTreeOrigin",
  "tree-country-select":"countryTreeId",
  "tree-country-model":"countryTreeModel",
  "tree-country-question":"countryTreeQuestion",
  "tree-country-year":"countryTreeYear"
 }[input.id];
 if(!key)return;
 state[key]=key==="countryTreeOrigin"||key==="countryTreeYear"?Number(input.value):input.value;
 state.countryTreeSelection=null;
 if(key==="countryTreeOrigin"){state.countryTreeId=null;state.countryTreeYear=null;}
 const graph=$("app").querySelector("[data-real-markov]");
 const scroll=graph?.scrollLeft||0;
 render();
 const next=$("app").querySelector("[data-real-markov]");
 if(next&&key!=="countryTreeOrigin")next.scrollLeft=scroll;
});
$("app").addEventListener("change",event=>{
  const select=event.target.closest?.("[data-public-question]");
  if(!select)return;
  const allowed=new Set(["atleast25","below25","entry","exit","persistence","stable_low"]);
  if(!allowed.has(select.value))return;
  state.markovQuestion=select.value;state.markovSelection=null;
  const graph=$("app").querySelector("[data-science-markov]");
  const scroll=graph?.scrollLeft||0;
  render();
  const next=$("app").querySelector("[data-science-markov]");
  if(next)next.scrollLeft=scroll;
});
$("app").addEventListener("click",async event=>{
 const graphNode=event.target.closest("[data-fnode],[data-fedge]");
 if(graphNode){
  const inRealTree=!!graphNode.closest("[data-country-tree]");
  if(inRealTree){
    const pair=String(graphNode.dataset.fnode||graphNode.dataset.fedge||"").split(":").map(Number);
    const catalog=getHistoricalCatalog(state.countryTreeOrigin);
    if(!catalog||pair.length!==2||!pair.every(Number.isInteger))return;
    const level=pair[0],stateIndex=pair[1];
    if(level<0||level>catalog.maxHorizon+1)return;
    if(graphNode.dataset.fnode!==undefined){
      if(stateIndex<0||stateIndex>3)return;
      state.countryTreeSelection={kind:"node",level,state:stateIndex};
    }else{
      // Edge indices are validated by the SVG generator; select only that actual edge.
      if(level<1||stateIndex<0||stateIndex>8)return;
      state.countryTreeSelection={kind:"edge",level,index:stateIndex};
    }
    const scroll=graphNode.closest("[data-real-markov]")?.scrollLeft||0;
    render();
    const next=$("app").querySelector("[data-real-markov]");
    if(next)next.scrollLeft=scroll;
    return;
  }
  const node=graphNode.dataset.fnode,edge=graphNode.dataset.fedge;
  const pair=String(node||edge||"").split(":").map(Number);
  if(pair.length!==2||!pair.every(Number.isInteger))return;
  if(node){
   if(pair[0]<0||pair[0]>2026-state.markovOrigin+1||pair[1]<0||pair[1]>3)return;
   state.markovSelection={kind:"node",level:pair[0],state:pair[1]};
  }else{
   const model=syntheticFourStateModel(2026-state.markovOrigin,state.markovOrigin);
   if(pair[0]<1||pair[0]>=model.levels.length||pair[1]<0||pair[1]>=model.levels[pair[0]].flows.length)return;
   state.markovSelection={kind:"edge",level:pair[0],index:pair[1]};
  }
  render();return;
 }
 const b=event.target.closest("button[data-action]");if(!b)return;
 const {action,value}=b.dataset;
 switch(action){
 case "navigate":navigate(value);break;
 case "question-priority":if(["P1","P2","P3"].includes(value)){state.questionPriority=value;render();}break;
 case "archive-page":state.archivePage=Number(value);render();break;
 case "archive-search":state.archiveQuery=$("archive-query").value;state.archivePage=0;render();break;
 case "scenario":state.scenario=value;render();break;
 case "program":state.program=value;navigate("overview");break;
 case "state-flow":state.flowState=value;render();break;
 case "markov-origin": {
    const y=Number(value);
    if(y!==2016&&y!==2020)break;
    state.markovOrigin=y;
    state.markovHorizon=2026-y;
    state.markovSelection=null;
    render();
    break;
  }
  case "markov-year": {
    const y=Number(value);
    if(!Number.isInteger(y)||y<1||y>2026-state.markovOrigin)break;
    state.markovHorizon=y;
    state.markovSelection=null;
    render();
    const strip=$("app").querySelector(".science-markov-panel .future-year-strip");
    const selected=strip?.querySelector(".future-year-select.active");
    if(selected&&strip)strip.scrollLeft=selected.offsetLeft-strip.offsetLeft-(strip.clientWidth-selected.clientWidth)/2;
    const chart=$("app").querySelector("[data-science-markov]");
    if(chart)chart.scrollLeft=Math.max(0,76+(y+1)*126-chart.clientWidth/2);
    break;
  }
 case "filter":state.filter=value;render();break;
  case "registry-filter":state.registryFilter=value;render();break;
  case "download-research-csv": {
   const url=URL.createObjectURL(new Blob([CSV_TEMPLATE],{type:"text/csv;charset=utf-8"}));
   const a=document.createElement("a");a.href=url;a.download="probabilities-example.csv";document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);break;
  }
 case "export-ideas":exportIdeas();break;
 case "make-video":makeVideo();break;
 case "copy-video":
  if(!state.videoText)makeVideo();
  try{await navigator.clipboard.writeText(state.videoText);if($("copy-status"))$("copy-status").textContent="Guion copiado.";}
  catch{if($("copy-status"))$("copy-status").textContent="Selecciona el texto para copiarlo manualmente.";}
  break;
 }
});
$("subtabs").addEventListener("click",event=>{
 const b=event.target.closest("button[data-action=navigate]");if(b)navigate(b.dataset.value);
});
$("app").addEventListener("keydown",event=>{
 if(event.key!=="Enter"&&event.key!==" ")return;
 const target=event.target.closest("[data-fnode],[data-fedge]");
 if(target){event.preventDefault();target.dispatchEvent(new MouseEvent("click",{bubbles:true}));}
});
$("app").addEventListener("change",event=>{
 if(event.target.id==="archive-table"){state.archiveTable=Number(event.target.value);state.archivePage=0;state.archiveQuery="";render();}
 if(event.target.id==="study-selector"){state.study=event.target.value;render();}
});
$("app").addEventListener("change",async event=>{
 if(event.target.id!=="research-csv")return;
 try{
  const file=event.target.files?.[0];if(!file)return;
  if(file.size>500000)throw Error("Archivo superior al tamaño admitido");
  state.registryOutput=evaluateLocalForecast(parseForecastCSV(await file.text()));
  render();
 }catch(error){
  state.registryOutput=null;render();
  const notice=document.createElement("p");notice.className="notice alert";
  notice.textContent="CSV rechazado: "+error.message;$("app").append(notice);
 }
});
$("app").addEventListener("submit",event=>{
 if(event.target.id!=="idea-form")return;
 event.preventDefault();const form=new FormData(event.target);
 const title=String(form.get("title")||"").trim(),question=String(form.get("question")||"").trim(),program=String(form.get("program")||"");
 if(!title||!question||title.length>110||question.length>600||!state.data.programs.some(p=>p.id===program))return;
 state.ideas.push({id:"LOCAL-"+(state.ideas.length+1),title,question,area:"Borrador local",links:[program]});
 render();
});
window.addEventListener("popstate",()=>{
 const view=new URLSearchParams(location.search).get("view");
 state.view=viewIds.has(view)?view:"brief";
 render();
});
load();
