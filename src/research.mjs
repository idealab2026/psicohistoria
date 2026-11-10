// Public research contracts: independently authored, no tracking or private services.
export const STAGES = Object.freeze(["propuesta", "fuente_identificada", "protocolo", "validacion_pendiente"]);

export function verifyResearch(data) {
  if (!data || data.schema_version !== 1 || data.class !== "public_research_program") throw Error("Unexpected research schema");
  if (data.forecast_issued !== 0 || data.prospective_results_verified !== 0) throw Error("Unverified issue counts");
  if (!Array.isArray(data.programs) || data.programs.length !== 7) throw Error("Incomplete public registry");
  const ids = new Set();
  for (const p of data.programs) {
    if (!/^[A-Z]{3}-\d{2}$/.test(p.id) || ids.has(p.id)) throw Error("Invalid research ID");
    ids.add(p.id);
    if (!STAGES.includes(p.stage) || p.skill_demonstrated !== false) throw Error("Unapproved research stage");
    for (const key of ["title","domain","question","outcome","baseline","next_gate","public_evidence"])
      if (typeof p[key] !== "string" || !p[key].trim()) throw Error("Incomplete research record: " + key);
    if (typeof p.source?.name !== "string" || typeof p.source?.url !== "string") throw Error("Source missing");
    const url = new URL(p.source.url);
    if (url.protocol !== "https:" || !["ucdp.uu.se","www.philadelphiafed.org","www.sec.gov","www.census.gov","www.usgs.gov"].includes(url.hostname) || url.username || url.password)
      throw Error("Source not on primary-source allowlist");
  }
  if (!/^2026-11-09-priorities-v1$/.test(data.agenda_version) ||
      typeof data.priority_method !== "string" || data.priority_method.length < 60 ||
      !Array.isArray(data.questions) || data.questions.length !== 10)
    throw Error("Incomplete useful questions research agenda");
  const questionIds = new Set();
  let p1=0,p2=0,p3=0;
  for (const q of data.questions) {
    if (!/^Q-[A-Z]{3}-\d{2}$/.test(q.id) || questionIds.has(q.id) || !ids.has(q.program))
      throw Error("Invalid or orphan scientific question");
    questionIds.add(q.id);
    if (q.priority === "P1") p1++;
    else if (q.priority === "P2") p2++;
    else if (q.priority === "P3") p3++;
    else throw Error("Unsupported scientific question priority");
    if (!["retrospectivo_no_prospectivo", "por_desarrollar", "fuente_pendiente"].includes(q.model_status) ||
        q.skill_demonstrated !== false) throw Error("Premature predictive skill claim");
    for (const key of ["question","target","horizon","baseline","decision","source_note","gate"])
      if (typeof q[key] !== "string" || q[key].trim().length < (key === "horizon" ? 2 : 12) || q[key].length > 500)
        throw Error("Scientific question missing measurable protocol: " + key);
  }
  if (p1 !== 3 || p2 !== 5 || p3 !== 2)
    throw Error("Unexpected scientific research prioritization");
  if (!Array.isArray(data.empirical_studies) || data.empirical_studies.length !== 1)
    throw Error("Incomplete empirical source-backed research inventory");
  for (const study of data.empirical_studies) {
    if (study.class !== "public_source_retrospective_evaluation" ||
        !data.questions.some(q=>q.id===study.linked_question) ||
        !/^EMP-[A-Z0-9.-]+$/.test(study.id) ||
        study.source_url !== "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-onset-251.csv" ||
        !/^[0-9a-f]{64}$/.test(study.source_sha256))
      throw Error("Empirical source provenance not validated");
    if (study.source_point_in_time_verified !== false ||
        study.prospective_validation !== false ||
        study.more_reliable_than_baseline_demonstrated !== false)
      throw Error("Retrospective results cannot be displayed as demonstrated forecast skill");
    for (const key of ["countries","observations","positive_events","cluster_bootstrap_replications"]) {
      if (!Number.isSafeInteger(study[key]) || study[key] < 1)
        throw Error("Invalid empirical observation count");
    }
    if (study.positive_events > study.observations || study.countries > study.observations)
      throw Error("Inconsistent empirical denominators");
    for (const key of ["brier_country","brier_global","brier_no_event","relative_brier_improvement","logloss_country","logloss_global"])
      if (typeof study[key] !== "number" || !Number.isFinite(study[key]))
        throw Error("Invalid empirical score");
    if (["brier_country","brier_global","brier_no_event"].some(key=>study[key]<0||study[key]>1) ||
        !Array.isArray(study.delta_brier_confidence_interval) ||
        study.delta_brier_confidence_interval.length!==2 ||
        !study.delta_brier_confidence_interval.every(Number.isFinite) ||
        study.delta_brier_confidence_interval[0]>study.delta_brier_confidence_interval[1])
      throw Error("Invalid empirical confidence interval or Brier score");
    if (typeof study.note!=="string" || !study.note.toLocaleLowerCase("es").includes("intervalo") || !study.note.toLocaleLowerCase("es").includes("no produce alertas"))
      throw Error("Missing robust retrospective limitation notice");
  }
  const r=data.riskset_study;
  if (!r || r.id!=="EMP-ONSET-251-RISKSET-20261110" ||
      r.linked_question!=="Q-GEO-01" ||
      r.status!=="RETROSPECTIVE_REVISED_VINTAGES_NOT_ASOF" ||
      r.point_in_time_verified!==false ||
      r.operational_utility_demonstrated!==false ||
      r.prospective_forecasts_issued!==0 ||
      r.exploratory_confidence_intervals!==true ||
      !Array.isArray(r.sources) || r.sources.length!==2 ||
      r.sources[0].sha256!=="e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a" ||
      r.sources[1].sha256!=="b49f7e80510d8a5779a52d872aef5b26456b3f5cbdd3ec32031339488e81813f" ||
      !r.sources.every(x=>typeof x.url==="string"&&x.url.startsWith("https://ucdp.uu.se/downloads/")) ||
      !Array.isArray(r.scenarios) || r.scenarios.length!==2)
    throw Error("Conditional UCDP scientific provenance or retrospective status invalid");
  if (r.scenarios[0].preceding_inactive_years!==1 ||
      r.scenarios[1].preceding_inactive_years!==2 ||
      !r.note?.includes("point-in-time") || !r.note?.includes("No es una alerta actual"))
    throw Error("Conditional UCDP sensitivity design is incomplete");
  for (const v of r.scenarios) {
    if (!Number.isSafeInteger(v.observations)||v.observations<100||
        !Number.isSafeInteger(v.countries)||v.countries<100||
        !Number.isSafeInteger(v.events)||v.events<=0||
        v.events>=v.observations||
        v.countries>=v.observations)
      throw Error("Conditional onset sample inconsistent");
    for (const key of ["brier_model","brier_baseline","brier_no_event",
                       "relative_brier_improvement","logloss_model","logloss_baseline"])
      if (typeof v[key]!=="number" || !Number.isFinite(v[key]) ||
          v[key]<0 || (key.startsWith("brier_") && v[key]>1))
        throw Error("Conditional Brier or log-loss invalid");
    if (!Array.isArray(v.cluster_delta_interval)||v.cluster_delta_interval.length!==2||
        !v.cluster_delta_interval.every(Number.isFinite)||
        v.cluster_delta_interval[0]>v.cluster_delta_interval[1])
      throw Error("Conditional onset interval invalid");
    if (Math.abs((1-v.brier_model/v.brier_baseline)-v.relative_brier_improvement)>1e-9)
      throw Error("Conditional onset improvement inconsistent with Brier values");
  }
  const rob=r.temporal_robustness;
  if (!rob || rob.status!=="EXPLORATORY_REVISED_VINTAGE_NOT_CONFIRMATORY" ||
      rob.independent_confirmation!==false ||
      rob.retrospective_point_in_time_verified!==false ||
      !/^[0-9]{8,15}$/.test(rob.workflow_run||"") ||
      !Array.isArray(rob.periods)||rob.periods.length!==4 ||
      !Array.isArray(rob.priors)||rob.priors.length!==6 ||
      !rob.note?.includes("DESPUÉS")||!rob.note?.includes("14 inicios"))
    throw Error("Temporal stability lacks exploratory design and provenance");
  for(const period of rob.periods){
    if(![1,2].includes(period.prior_inactive_years) ||
       !["2010-2016","2017-2024"].includes(period.years) ||
       !Number.isInteger(period.observations)||period.observations<100||
       !Number.isInteger(period.events)||period.events<1||
       !Number.isFinite(period.relative_brier_improvement)||
       !Array.isArray(period.confidence_delta_brier)||period.confidence_delta_brier.length!==2||
       !period.confidence_delta_brier.every(Number.isFinite))
      throw Error("Temporal stability score inconsistent");
  }
  for(const p of rob.priors){
    if(![1,2].includes(p.prior_inactive_years)||![5,20,100].includes(p.prior_strength)||
       !Number.isFinite(p.relative_brier_improvement)||
       !Array.isArray(p.confidence_delta_brier)||p.confidence_delta_brier.length!==2||
       !p.confidence_delta_brier.every(Number.isFinite))
      throw Error("Shrinkage sensitivity not valid");
  }
  const p20=rob.priors.filter(x=>x.prior_strength===20);
  if(p20.length!==2||p20.some(x=>Math.abs(x.relative_brier_improvement-
      r.scenarios.find(v=>v.preceding_inactive_years===x.prior_inactive_years).relative_brier_improvement)>1e-10))
    throw Error("Sensitivity does not reproduce primary fixed prior");
  const v=data.historical_vintage_2024;
  if(!v||v.id!=="EMP-ONSET-231-251-CROSS-RELEASE-2024"||
     v.analysis_type!=="RETROSPECTIVE_CROSS_RELEASE_NOT_ACTUALLY_ISSUED"||
     v.linked_question!=="Q-GEO-01"||
     v.training_last_year!==2022||v.year!==2024||
     v.sample_size!==160||v.positives!==1||
     v.model_issued_before_event!==false||
     v.prospective_skill_demonstrated!==false||
     v.historical_release_timing_cryptographically_verified!==false||
     v.actual_train_features_from_target_year!==false||
     v.too_few_events_for_skill_inference!==true||
     !Array.isArray(v.sources)||v.sources.length!==3||
     v.sources[0].sha256!=="e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289"||
     v.sources[1].sha256!=="8fe95d8a5780cba1d312f9673ffd9e93b90c91bb26e348393a583853a892b718"||
     v.sources[2].sha256!=="e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a"||
     !v.sources.every(x=>x.url.startsWith("https://ucdp.uu.se/downloads/")))
      throw Error("Invalid real archived vintage scientific provenance");
  for(const k of ["brier_model","brier_global","logloss_model","logloss_global","relative_brier_skill"])
    if(typeof v[k]!=="number"||!Number.isFinite(v[k]))throw Error("Invalid vintage holdout scores");
  if(!(v.logloss_model>0&&v.logloss_global>0&&v.logloss_model<v.logloss_global))
    throw Error("Archived vintage log-loss disagreement cannot be misreported");
  if(!(v.brier_model>v.brier_global&&v.brier_global>0&&
       v.relative_brier_skill<0&&
       Math.abs(v.relative_brier_skill-(1-v.brier_model/v.brier_global))<1e-9)||
     !Array.isArray(v.uncertainty_brier_delta)||v.uncertainty_brier_delta.length!==2||
     !v.uncertainty_brier_delta.every(Number.isFinite)||
     !(v.uncertainty_brier_delta[0]<0&&v.uncertainty_brier_delta[1]>0)||
     !v.conclusion.includes("no se reproduce")||!v.caveat.includes("2023"))
      throw Error("Vintage result obscures negative or uncertain finding");
  const drift=data.historical_label_revisions;
  if(!drift || drift.id!=="EMP-ONSET-231-251-LABEL-DRIFT-20261110" ||
     drift.linked_question!=="Q-GEO-01" ||
     drift.status!=="RETROSPECTIVE_CROSS_RELEASE_LABEL_REVISION_NOT_FORECAST" ||
     drift.period!=="1946–2022" || drift.observations!==12161 ||
     drift.labels_flipped!==2 || drift.flips_zero_to_one!==1 ||
     drift.flips_one_to_zero!==1 || drift.positives_23_1!==242 ||
     drift.positives_25_1!==242 ||
     drift.country_years_only_in_23_1!==0 ||
     drift.country_years_only_in_25_1!==0 ||
     drift.historical_release_dates_verified!==false ||
     drift.prospective_skill_demonstrated!==false ||
     !Array.isArray(drift.changes_by_year) ||
     JSON.stringify(drift.changes_by_year)!==JSON.stringify([
       {year:2018,flips_zero_to_one:1,flips_one_to_zero:0},
       {year:2021,flips_zero_to_one:0,flips_one_to_zero:1}]) ||
     !Array.isArray(drift.source_sha256s) ||
     drift.source_sha256s[0]!==v.sources[0].sha256 ||
     drift.source_sha256s[1]!==v.sources[2].sha256 ||
     !Array.isArray(drift.source_urls) ||
     drift.source_urls[0]!==v.sources[0].url ||
     drift.source_urls[1]!==v.sources[2].url ||
     !drift.note?.includes("No es un pronóstico"))
    throw Error("Public historical onset revision claims lack verified provenance or safety boundary");
  const e=data.external_vintage_holdout;
  if(!e || e.id!=="EMP-ONSET-171-231-251-CROSS-RELEASE-20261110" ||
     e.linked_question!=="Q-GEO-01" || e.study_date!=="2026-11-10" ||
     e.status!=="RETROSPECTIVE_CROSS_RELEASE_NOT_HISTORICALLY_ISSUED" ||
     e.schema!=="idealab.psico.cross_release_external_holdout.v1" ||
     e.training_since!==2000 || e.country_prior_strength!==20 ||
     e.historical_release_timing_cryptographically_verified!==false ||
     e.point_in_time_verified!==false ||
     e.prospective_predictions_issued!==0 ||
     e.operational_utility_demonstrated!==false ||
     e.more_reliable_than_global_demonstrated!==false ||
     e.unit_comparability_verified!==false ||
     e.interpretation_downgraded!==true ||
     !e.unit_comparability_note?.includes("no constituye un backtest homogéneo") ||
     e.exploratory_confidence_intervals!==true ||
     e.legacy_19_1_duplicates?.duplicate_country_year_keys!==47 ||
     e.legacy_19_1_duplicates?.contradictory_onset2_keys!==13 ||
     e.legacy_19_1_duplicates?.choice_made_after_data_diagnostics!==true ||
     !e.legacy_source_version_caveat?.includes("2017, not 2018") ||
     !e.disclaimer?.includes("not an actual historical issue") ||
     !e.explanatory_note?.includes("no se acreditan emisiones históricas"))
    throw Error("Unverified cross-release forecasting claim or unsupported provenance");
  const expectedSources=[
     ["19.1",2017,"ba54aeace175173b7643a2c14ba35ce89a2fcfd31712085e4fd13de656f752a8"],
     ["23.1",2022,"e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289"],
     ["25.1",2024,"e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a"]
  ];
  if(!expectedSources.every(([version,last,sha])=>
     e.sources?.[version]?.last_year===last &&
     e.sources[version].sha256===sha &&
     e.sources[version].url.startsWith("https://ucdp.uu.se/downloads/onset/")))
    throw Error("Cross-release official source hash or cutoff mismatch");
  const periods=e.studies?.flatMap(s=>s.years.map(y=>({year:y.year,n:y.n,events:y.events})));
  if(!Array.isArray(e.studies)||e.studies.length!==2||
     e.studies[0].origin_version!=="19.1"||e.studies[0].outcome_version!=="23.1"||
     e.studies[1].origin_version!=="23.1"||e.studies[1].outcome_version!=="25.1"||
     JSON.stringify(periods)!==JSON.stringify([
        {year:2020,n:173,events:2},
        {year:2021,n:173,events:1},
        {year:2022,n:173,events:3},
        {year:2024,n:196,events:1}]))
    throw Error("Cross-release target years and events differ from source-backed experiment");
  const a=e.aggregate;
  if(a?.country_years!==715||a.events!==7||
     ![a.brier_model,a.brier_global,a.brier_no_event,
       a.logloss_model,a.logloss_global,a.relative_brier_skill_global].every(Number.isFinite)||
     !(a.brier_model>a.brier_global&&a.brier_global>a.brier_no_event&&
       a.logloss_model>a.logloss_global&&a.relative_brier_skill_global<0)||
     Math.abs(a.relative_brier_skill_global-(1-a.brier_model/a.brier_global))>1e-10)
    throw Error("Cross-release negative score cannot be presented as positive");
  const ci=a.cluster_bootstrap?.global?.delta_brier_95pct_interval;
  if(!Array.isArray(ci)||ci.length!==2||
     !ci.every(Number.isFinite)||ci[0]<=0||ci[1]<=ci[0]||
     a.cluster_bootstrap?.global?.replications!==2000||
     a.cluster_bootstrap?.global?.resampling_unit!=="country"||
     !Number.isFinite(e.legacy_duplicate_exclusion_sensitivity?.relative_brier_skill_global)||
     e.legacy_duplicate_exclusion_sensitivity.relative_brier_skill_global>=0)
    throw Error("Cross-release uncertainty, provenance or sensitivity not validated");
  const rs=data.recency_sensitivity_study;
  if(!rs || rs.id!=="EMP-ONSET-231-251-RECENCY-20261110" ||
     rs.linked_question!=="Q-GEO-01" ||
     rs.analysis_date!=="2026-11-10" ||
     rs.schema!=="idealab.psico.recency_sensitivity.v1" ||
     rs.status!=="EXPLORATORY_POSTHOC_NOT_PROSPECTIVE" ||
     rs.legacy_19_1_excluded_due_to_country_year_unit_mismatch!==true ||
     rs.training_start!==2000 || rs.country_prior_strength!==20 ||
     JSON.stringify(rs.windows_years)!==JSON.stringify([5,10,20]) ||
     JSON.stringify(rs.source_vintages)!==JSON.stringify(["23.1","25.1"]) ||
     rs.source_sha256?.["23.1"]!==e.sources["23.1"].sha256 ||
     rs.source_sha256?.["25.1"]!==e.sources["25.1"].sha256 ||
     rs.source_urls?.["23.1"]!==e.sources["23.1"].url ||
     rs.source_urls?.["25.1"]!==e.sources["25.1"].url ||
     rs.prospective_forecasts_issued!==0 ||
     rs.skill_demonstrated!==false ||
     rs.source_release_dates_verified!==false ||
     rs.new_independent_confirmatory_holdout!==false ||
     !rs.caveat?.includes("después de ver") ||
     !rs.conclusion?.includes("excluded from this assessment"))
    throw Error("Recency experiment is not a verified cross-release exploratory study");
  const inner=rs.internally_revised_vintage,outer=rs.cross_release_holdout_2024;
  if(inner?.assessment!=="SAME_VINTAGE_REVISED_DATA_LEAKAGE_NOT_HISTORICALLY_ASOF" ||
     inner.n!==1568||inner.events!==22 ||
     JSON.stringify(inner.tested_years)!==JSON.stringify([2015,2016,2017,2018,2019,2020,2021,2022]) ||
     !Array.isArray(inner.annual_events)||inner.annual_events.length!==8 ||
     inner.annual_events.reduce((n,v)=>n+v.events,0)!==22 ||
     !inner.annual_events.every(v=>v.n===196) ||
     outer?.assessment!=="EXTERNAL_VINTAGE_LABELS_BUT_2024_PREVIOUSLY_EXAMINED" ||
     outer.year!==2024 || outer.training_last_year!==2022 ||
     outer.n!==196||outer.events!==1)
    throw Error("Recency temporal comparison or sample coverage manipulated");
  const candidateNames=["country_10","country_20","country_5","country_full",
                         "global_10","global_20","global_5","global_full"];
  for(const metrics of [inner.pooled_metrics,outer.metrics]){
    if(!metrics || candidateNames.some(k=>!metrics[k]||
       !Number.isFinite(metrics[k].brier)||metrics[k].brier<0||metrics[k].brier>1||
       !Number.isFinite(metrics[k].logloss)||metrics[k].logloss<0)||
       metrics.no_event?.logloss!==null ||
       !Number.isFinite(metrics.no_event?.brier))
      throw Error("Recency scientific metrics incomplete or invalid");
  }
  const near=(a,b)=>Math.abs(a-b)<1e-10;
  if(!near(outer.metrics.global_full.brier, e.studies[1].years[0].brier_global)||
     !near(outer.metrics.country_full.brier,e.studies[1].years[0].brier_model)||
     !(outer.metrics.country_5.brier>outer.metrics.global_5.brier &&
       outer.metrics.global_5.brier<outer.metrics.global_full.brier &&
       inner.pooled_metrics.country_full.brier>inner.pooled_metrics.global_full.brier))
    throw Error("Recency sensitivity must preserve cross-source negative Brier and reference");
  return true;
}
const EXPECTED = "issued_at,input_available_at,event_start,event_end,outcome_verified_at,model_probability,baseline_probability,outcome";
export function parseForecastCSV(csv) {
  if (typeof csv !== "string" || csv.length > 500000) throw Error("Invalid local dataset size");
  const lines = csv.trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2 || lines.length > 2001 || lines[0].trim() !== EXPECTED) throw Error("Unexpected CSV columns or row count");
  return lines.slice(1).map((line, idx) => {
    const v = line.split(",").map(x=>x.trim());
    if (v.length !== 8) throw Error("Column mismatch on line " + (idx + 2));
    return Object.fromEntries(EXPECTED.split(",").map((key,i)=>[key,v[i]]));
  });
}
function isoDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(Date.parse(value)) || new Date(value).toISOString().slice(0,10) !== value)
    throw Error("A real ISO calendar date is required");
  return value;
}
export function evaluateLocalForecast(rows) {
  if (!Array.isArray(rows) || rows.length < 1 || rows.length > 2000) throw Error("Invalid local sample");
  let model=0, baseline=0;
  for (const row of rows) {
    const available=isoDate(row.input_available_at), issued=isoDate(row.issued_at),
      start=isoDate(row.event_start), end=isoDate(row.event_end), verified=isoDate(row.outcome_verified_at);
    if (!(available <= issued && issued < start && start <= end && end < verified)) throw Error("Temporal admissibility violation");
    for (const key of ["model_probability","baseline_probability"])
      if (!/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(row[key])) throw Error("Invalid probability");
    if (!/^[01]$/.test(row.outcome)) throw Error("Invalid outcome");
    const p=Number(row.model_probability), b=Number(row.baseline_probability), y=Number(row.outcome);
    model+=(p-y)**2;baseline+=(b-y)**2;
  }
  const n=rows.length, model_brier=model/n, baseline_brier=baseline/n;
  return {n,model_brier,baseline_brier,relative_skill:baseline_brier>0?1-model_brier/baseline_brier:null,
    verified_independently:false,notice:"Cálculo local. La autenticidad de fechas, fuentes y resoluciones NO se ha verificado."};
}
export const CSV_TEMPLATE = EXPECTED+"\n2024-02-01,2024-01-31,2024-03-01,2024-03-31,2024-04-10,0.7,0.5,1\n2024-02-01,2024-01-31,2024-03-01,2024-03-31,2024-04-10,0.2,0.5,0\n";
