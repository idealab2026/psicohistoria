/** 4 separately validated future evaluation contracts; 0 actually observed labels.
 * Never infer scores, events, IID counts or "certified" status from issued p.
 */
import {validateProspectiveRegistry,ORIGINAL_SHA,ORIGINAL_COMMITS} from "./prospective-registry.mjs";
import {validateIssuedGEO2028,GEO2028_FORECAST_SHA,GEO2028_FIRST_COMMIT} from "./prospective-2028.mjs";

const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({
 "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
const ORDER=["GEO2027","NEWCONF2027","ACD2027","GEO2028"];
const COUNT=[196,196,32,196],PROVISIONAL_MIN=[187,187,32,196];
const TARGET=[2027,2027,2027,2028];
const HORIZON=[2,2,2,3];
const DATE=["2028-01-01","2028-01-01","2028-01-01","2029-01-01"];
const PRIMARY=["p_model","p_model","p_global_recent5","p_model"];
const COMPARE=["p_baseline_global_5y","p_baseline_global_5y","p_country_eb","p_baseline_global_5y"];
const SCRIPTS=[
 "scripts/evaluate_2027_official.py",
 "scripts/evaluate_2027_newconf_official.py",
 "scripts/evaluate_acd2027_retention_official.py",
 "scripts/evaluate_geo2028_first_complete_official.py"
];
const SOURCE=["UCDP OrganizedViolenceCY","UCDP Intrastate Country Level Multiple Onset",
 "UCDP/PRIO Armed Conflict Dataset","UCDP OrganizedViolenceCY"];
const SHAS=[ORIGINAL_SHA.GEO2027,ORIGINAL_SHA.NEWCONF2027,
 ORIGINAL_SHA.ACD2027,GEO2028_FORECAST_SHA];
const COMMITS=[ORIGINAL_COMMITS.GEO2027,ORIGINAL_COMMITS.NEWCONF2027,
 ORIGINAL_COMMITS.ACD2027,GEO2028_FIRST_COMMIT];
const base="https://github.com/idealab2026/psicohistoria/";
const complete=(x,y)=>x===y;
export function verifyFutureEvaluationContracts(
 report,original2027,original2028,manifest2028
){
 validateProspectiveRegistry(original2027);
 validateIssuedGEO2028(original2028,manifest2028,original2027);
 if(!report||
   report.schema!=="idealab.psico.future_evaluation_contract_registry.v1"||
   report.status!=="FOUR_ISSUED_COHORTS_ZERO_OFFICIAL_CERTIFIED_LABELS"||
   report.publication_purpose!=="READ_ONLY_EVALUATION_CONTRACT_NOT_2027_2028_OUTCOME"||
   report.first_issued_2027_country_endpoint_questions!==424||
   report.additional_issued_GEO2028_country_questions!==196||
   report.total_issued_country_endpoint_year_questions!==620||
   report.n_forecast_emissions!==4||
   report.n_future_outcomes_independently_certified!==0||
   report.n_official_scoring_reports_certified!==0||
   report.n_independent_country_year_trials_claimed!==0||
   report.cross_endpoint_country_overlap_present!==true||
   report.cross_year_2027_2028_GEO_origin_overlap_present!==true||
   report.global_prospective_skill_demonstrated!==false||
   report.first_complete_source_must_be_independently_attested!==true||
   report.first_public_utc_is_github_metadata_not_independent_notary!==true||
   report.never_treat_exploratory_score_as_certified!==true||
   report.never_pool_Brier_or_country_years_from_distinct_endpoints!==true||
   report.never_claim_IID_country_bootstrap_significance!==true||
   !Array.isArray(report.ordered_cohorts)||
   report.ordered_cohorts.join("|")!==ORDER.join("|")||
   !Array.isArray(report.cohorts)||report.cohorts.length!==4)
   throw Error("REGISTRO_EVALUACION_FUTURA_NO_AUTENTICADO");
 const originalCohort=original2027.cohorts;
 for(let i=0;i<4;i++){
   const e=report.cohorts[i],id=ORDER[i],n=COUNT[i];
   if(!e||e.cohort!==id||
      e.forecast_sha256!==SHAS[i]||
      e.first_public_forecast_commit!==COMMITS[i]||
      e.first_public_forecast_utc!==(
        i<3?originalCohort[id].issue_utc:manifest2028.first_public_forecast_commit_utc
      )||
      e.origin_year!==2025||e.target_year!==TARGET[i]||
      e.horizon_years!==HORIZON[i]||
      e.target_year-e.origin_year!==e.horizon_years||
      e.issued_country_questions!==n||
      e.original_issued_country_questions_unresolved!==n||
      e.future_country_labels_certified!==0||
      e.provisional_score_min_coverage!==PROVISIONAL_MIN[i]||
      e.complete_source_coverage_required_for_certification!==n||
      e.first_eligible_source_date!==DATE[i]||
      e.primary_field!==PRIMARY[i]||
      e.primary_comparison_field!==COMPARE[i]||
      e.source_family!==SOURCE[i]||
      e.evaluation_script!==SCRIPTS[i]||
      e.source_independently_verified_full_future_release!==false||
      e.official_scores_certified!==false||
      e.candidate_scores_available_now!==false||
      e.iid_country_bootstrap_disabled_in_official_candidate_evaluator!==true||
      e.statistical_confidence_interval_claimed!==false||
      e.sharp_missing_label_brier_region_available!==(id==="GEO2027"||id==="NEWCONF2027")||
      e.prospective_skill_demonstrated!==false||
      e.independently_notarized!==false||
      e.provisional_scoring_is_never_certification!==true||
      e.depends_on_same_2025_origin_as_GEO2027!==(id==="GEO2028")||
      e.official_first_candidate_version!==(id==="GEO2028"?"29.1":"28.1")||
      typeof e.event_definition!=="string"||e.event_definition.length<35||
      typeof e.coverage_basis!=="string"||e.coverage_basis.length<30||
      typeof e.experimental_interval_warning!=="string"||
      e.experimental_interval_warning.length<30||
      !Array.isArray(e.secondary_model_fields))
     throw Error("COHORTE_O_CONTRATO_DE_EVALUACION_MODIFICADO");
   if(i<3&&(originalCohort[id].forecast_sha256!==e.forecast_sha256||
      originalCohort[id].fixed_country_count!==n||
      originalCohort[id].primary_model!==e.primary_field))
     throw Error("REGISTRO_2027_PREVIO_MODIFICADO");
   if(i===3&&(e.forecast_sha256!==manifest2028.forecast_sha256||
      e.issued_country_questions!==original2028.countries.length))
     throw Error("EMISION_GEO2028_MODIFICADA");
 }
 return report;
}

export function renderFutureEvaluationContracts(
 report,original2027,original2028,manifest2028
){
 if(!report||!original2027||!original2028||!manifest2028)
  return '<header class="section-head"><h2>Evaluaciones futuras</h2>'+
   '<p>Registro conjunto no disponible o sin autenticar. No se muestran puntuaciones.</p></header>';
 verifyFutureEvaluationContracts(report,original2027,original2028,manifest2028);
 const totals=[
  ["4","Emisiones con evaluación futura preparada"],
  ["620","Preguntas país × variable × año emitidas"],
  ["0","Resultados futuros certificados"],
  ["0","Informes oficiales de acierto certificados"]
 ].map(([n,label])=>'<div><strong>'+n+'</strong><span>'+esc(label)+'</span></div>').join("");
 const human={
  GEO2027:"Violencia estatal · 2027",
  NEWCONF2027:"Nuevos conflictos · 2027",
  ACD2027:"Persistencia intraestatal · 2027",
  GEO2028:"Violencia estatal · 2028"
 };
 const cards=report.cohorts.map(e=>
  '<article class="prospective-cohort-card future-eval-card">'+
   '<div class="eyebrow">'+esc(e.cohort)+'</div>'+
   '<strong>'+esc(human[e.cohort])+'</strong>'+
   '<p>'+esc(e.event_definition)+'</p>'+
   '<div class="tiny">Origen '+e.origin_year+' → objetivo '+e.target_year+
   ' · '+e.horizon_years+' años · '+e.issued_country_questions+' países</div>'+
   '<div class="future-eval-progress"><span>0 / '+e.issued_country_questions+
   ' resultados certificados</span><i aria-hidden="true"></i></div>'+
   '<p class="tiny">Primera fuente candidata: <strong>'+esc(e.first_eligible_source_date)+
   '</strong> · UCDP '+esc(e.official_first_candidate_version)+'</p>'+
   '<a href="'+base+'commit/'+e.first_public_forecast_commit+
   '" target="_blank" rel="noopener noreferrer">Primera emisión verificable</a></article>'
 ).join("");
 const rows=report.cohorts.map(e=>
  '<tr><td data-label="Emisión"><strong>'+esc(e.cohort)+
   '</strong><small>'+esc(e.source_family)+'</small></td>'+
  '<td data-label="Modelo"><strong>'+esc(e.primary_field.replaceAll("_"," "))+
   '</strong><small>Contra '+esc(e.primary_comparison_field.replaceAll("_"," "))+'</small></td>'+
  '<td data-label="Cobertura"><strong>'+e.provisional_score_min_coverage+
   ' / '+e.issued_country_questions+'</strong><small>Mínimo de cálculo exploratorio</small>'+
   '<small>Certificación: '+e.complete_source_coverage_required_for_certification+
   '/'+e.issued_country_questions+' + auditoría de fuente</small>'+
   '<small>'+esc(e.sharp_missing_label_brier_region_available?
       'Cotas de Brier ante datos faltantes · no IC':
       'Sin intervalos IID')+'</small></td>'+
  '<td data-label="Fuente"><strong>'+esc(e.official_first_candidate_version)+
   '</strong><small>Primera fecha posible '+esc(e.first_eligible_source_date)+'</small></td>'+
  '<td data-label="Estado"><span class="prospective-pending">Sin resultados</span>'+
   '<small>0 etiquetas · 0 puntuaciones certificadas</small></td>'+
  '<td data-label="Protocolo"><a href="'+base+'blob/main/'+
   esc(e.evaluation_script)+'" target="_blank" rel="noopener noreferrer">'+
   'Evaluador técnico</a><small>'+esc(e.coverage_basis)+'</small></td></tr>'
 ).join("");
 return '<header class="section-head">'+
  '<div class="eyebrow">PSICOHISTORIA · CONTRATOS DE RESOLUCIÓN FUTURA</div>'+
  '<h2>Estado de las evaluaciones prospectivas</h2>'+
  '<p>Cuatro emisiones reales con reglas de evaluación distintas. Se separan el umbral '+
  'para un cálculo provisional, la cobertura necesaria y la certificación externa '+
  'de la fuente. <strong>Ningún resultado futuro está certificado.</strong></p></header>'+
  '<div class="prospective-stats">'+totals+'</div>'+
  '<div class="prospective-cohorts future-eval-cohorts">'+cards+'</div>'+
  '<section class="panel"><div class="eyebrow">PRÓXIMA COHORTE · PRE-REGISTRADA · NO EMITIDA</div>'+
  '<h3>GEO2028 · Nuevo origen 2026, horizonte dos años</h3>'+
  '<p>El modelo y los comparadores ya están definidos antes de recibir la edición anual '+
  'UCDP OrganizedViolenceCY 27.1, pendiente en la comprobación del 15/11/2026. '+
  '<strong>0 probabilidades emitidas con origen 2026.</strong> No sustituir por '+
  'datos mensuales provisionales ni inventar resultados.</p>'+
  '<p class="tiny">La futura emisión utilizaría 2026 → 2028, distinto del '+
  'GEO2028 ya emitido con 2025 → 2028. Compartirán el mismo objetivo 2028 '+
  'y no constituirán dos ensayos independientes. La cohorte 2026 puede '+
  'tener países distintos y revisiones históricas.</p>'+
  '<p><a href="'+base+'blob/main/docs/geo2028-origin2026-preregistration.md" '+
  'target="_blank" rel="noopener noreferrer">Ver protocolo previo a los datos de 2026</a></p></section>'+
  '<section class="panel"><h3>Condiciones para poder puntuar cada emisión</h3>'+
  '<div class="prospective-table-wrap"><table class="prospective-table future-eval-table">'+
  '<thead><tr><th>Emisión</th><th>Modelo y referencia</th><th>Cobertura</th>'+
  '<th>Edición y fecha</th><th>Estado</th><th>Contrato</th></tr></thead>'+
  '<tbody>'+rows+'</tbody></table></div></section>'+
  '<p class="notice info"><strong>Importante:</strong> 187/196 permite una puntuación '+
  '<em>exploratoria</em> en GEO2027 y NEWCONF2027, pero no certificación. '+
  'ACD2027 requiere revisar la codificación de sus 32 países y GEO2028 exige '+
  '196 etiquetas explícitas. Cada fuente oficial futura debe verificarse externamente '+
  'antes de reconocer cualquier desempeño.</p>'+
  '<p class="notice info"><strong>Corrección metodológica:</strong> '+ 
  'se han desactivado los bootstrap IID por países de GEO2027 y NEWCONF2027. '+
  'En su lugar, sus evaluadores calculan límites matemáticos exactos del Brier '+
  'de los 196 países cuando faltan resultados. Son <strong>cotas de identificación, '+
  'no intervalos de confianza</strong>; no asignan probabilidades a los eventos ni '+
  'sustituyen la certificación de los datos futuros.</p>'+
  '<p class="notice info">Las 620 preguntas comparten países, años y orígenes de '+
  'forma parcial; no son 620 ensayos independientes. Los Brier de variables '+
  'diferentes no se agregan ni se presentan como habilidad predictiva '+
  'demostrada. Las fechas de GitHub son metadatos públicos, no notarización externa.</p>';
}
