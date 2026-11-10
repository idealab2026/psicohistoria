import {verify,score,calibration} from "./metrics.mjs";
import {verifyResearch,parseForecastCSV,evaluateLocalForecast,CSV_TEMPLATE} from "./research.mjs";
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
const state={archive:null,projectCatalog:null,archiveTable:0,archiveQuery:"",archivePage:0,data:null,research:null,registryFilter:"todos",registryOutput:null,questionPriority:"P1",view:viewIds.has(new URLSearchParams(location.search).get("view"))?new URLSearchParams(location.search).get("view"):"brief",scenario:null,program:null,study:null,filter:"todos",ideas:[],flowState:"00",markovOrigin:2020,markovHorizon:6,markovQuestion:"atleast25",markovSelection:null,countryTreeOrigin:2020,countryTreeId:null,countryTreeModel:"country_shrinkage",countryTreeQuestion:"atleast25",countryTreeYear:null,countryTreeSelection:null,videoText:"",busy:false};
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
 return section("INICIO · ESTADO PÚBLICO","Próximos pasos y resultados","Preparar, publicar y demostrar utilidad son hitos distintos. Las cifras de esta web son ilustrativas y no constituyen evidencia predictiva.")+
 scientificNeuralPanel(d.programs,state.program)+
 box('<div class="item-row wrap"><div><h3>Registro público experimental</h3><p>Versión funcional con muestras sintéticas y revisión de procedimientos.</p></div>'+tag("Sin predicciones reales","alert")+'</div>'+
 '<div class="section-grid three"><div><div class="card-number">'+d.programs.length+'</div><div class="tiny">Líneas de estudio</div></div><div><div class="card-number">'+ready+'/'+d.milestones.length+'</div><div class="tiny">Pasos técnicos verificados</div></div><div><div class="card-number">0</div><div class="tiny">Pronósticos prospectivos acreditados</div></div></div>','highlight')+
 section("LECTURA RÁPIDA","Qué se puede explorar","Cada módulo tiene un propósito concreto y muestra los supuestos, las fuentes y las limitaciones de los ejemplos.")+
 cards([
 ["Árbol de futuros","Escenarios alternativos y supuestos explícitos. No son pronósticos.", "navigate","futures"],
 ["Evidencia y modelos","Evaluación probabilística sintética comparada con un baseline.", "navigate","science"],
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
 return section("PREDICCIONES · OBSERVATORIO","Riesgos 2027","Protocolo de observación futura. Un ranking experimental no equivale a probabilidades emitidas, y no debe publicarse sin comprobar origen, licencia y disponibilidad histórica.")+
 '<div class="section-grid four">'+[
 ["Cobertura de países","No disponible"],["Emisiones preregistradas","0"],["Resoluciones independientes","0"],["Validez prospectiva","No acreditada"]
 ].map(([k,v])=>box('<div class="tiny">'+safe(k)+'</div><div class="card-number">'+safe(v)+'</div>')).join("")+'</div>'+
 box('<h3>Condiciones para activar un observatorio público</h3><ul class="compact-list"><li>Universo, eventos y horizontes fijados ex ante.</li><li>Fuentes geográficas y temporales con derecho de redistribución.</li><li>Disponibilidad de cada variable antes del origen de predicción.</li><li>Probabilidades firmadas y selladas antes del desenlace.</li><li>Evaluación posterior contra referencia y publicación de errores.</li></ul>'+msg("No se publican puntuaciones por país ni un listado de riesgos porque aún no existe un dataset público independiente aprobado."),"soft")+
 section("ESTADO","Registro de emisiones","Ausencia explícita de emisiones; no se deduce capacidad predictiva de un conjunto de pruebas sintéticas.")+
 box('<div class="tiny">PREDICCIONES PÚBLICAS EMITIDAS</div><h3>Sin registros</h3><p>El módulo permanecerá sin cifras de riesgo hasta disponer de fuentes point-in-time y de un protocolo de publicación verificable.</p>');
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
 return renderVintageHoldout()+renderConditionalRisksetEvidence()+renderEmpiricalEvidence()+section("INVESTIGACIÓN · DEMOSTRACIONES","Pruebas sintéticas del evaluador","La tabla siguiente usa muestras inventadas para probar el software; no debe confundirse con el contraste UCDP real mostrado arriba.")+
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
  const [response,researchResponse]=await Promise.all([fetch("./data/demo.json",{cache:"no-store"}),fetch("./data/research.json",{cache:"no-store"})]);
   if(!response.ok||!researchResponse.ok)throw new Error("Public sources unavailable");
   const [data,research]=await Promise.all([response.json(),researchResponse.json()]);
   verify(data);verifyResearch(research);state.research=research;
  // Detailed scientific records are intentionally not read by the public client.
  state.projectCatalog=(await catalogRead).data;
  for(const key of ["programs","milestones","ideas"])if(!Array.isArray(data[key]))throw new Error("Incomplete public catalogue");
  state.data=data;state.scenario=state.scenario||data.branches[0].id;state.program=state.program||data.programs[0].id;state.study=state.study||data.studies[0].id;
  $("count-studies").textContent=data.studies.length;$("count-models").textContent=data.programs.length;
  $("count-predictions").textContent="1177";$("count-evaluated").textContent="0";
  $("as-of").textContent="Archivo histórico y demostraciones separadas";
  $("sync-status").textContent="Vista pública agregada · sin resultados prospectivos acreditados";
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
