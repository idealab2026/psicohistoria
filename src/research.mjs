// Public research contracts: independently authored, no tracking or private services.
export const STAGES = Object.freeze(["propuesta", "fuente_identificada", "protocolo", "validacion_pendiente"]);

export function verifyResearch(data) {
  if (!data || data.schema_version !== 1 || data.class !== "public_research_program") throw Error("Unexpected research schema");
  if (data.forecast_issued !== 1 || data.prospective_results_verified !== 0) throw Error("Invalid issued/prospective result counts");
  const issued=data.prospective_2027_issue;
  if(!issued || issued.question!=="Q-GEO-2027-01" ||
     issued.forecast_id!=="PSICO-GEO2027-STATEBASED25-V1" ||
     issued.publication_class!=="PROSPECTIVE_ISSUED_UNRESOLVED" ||
     issued.year!==2027 || issued.source_observed_through!==2025 ||
     issued.countries_issued!==196 || issued.outcomes_resolved!==0 ||
     issued.skill_demonstrated!==false || issued.independently_notarized!==false ||
     issued.forecast_document_sha256!=="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5" ||
     issued.preregistered_protocol_main_commit!=="87959a117e1b30323392a488c48c9afb1cb0bffc" ||
     issued.first_public_forecast_commit!=="3bb3561c8d6182c30624591276c705fb76ce99dc" ||
     issued.first_public_utc!=="2026-11-10T17:23:12Z" ||
     issued.manifest_path!=="data/forecast-2027-manifest.json" ||
     issued.data_path!=="data/forecast-2027-ucdp261.json" ||
     !issued.note?.includes("distinta de onset2"))
    throw Error("Unverified or mutated GEO-2027 prospective issuance");
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
  const backtest=data.statebased_2027_spec_backtest;
  if(!backtest ||
    backtest.id!=="EMP-GEO2027-MODEL-2012-2025-RETROSPECTIVE-V1" ||
    backtest.source_dataset!=="UCDP OrganizedViolenceCY 26.1" ||
    backtest.source_sha256!=="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34" ||
    backtest.source_url!=="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip" ||
    backtest.report_path!=="data/forecast-2027-historical-backtest.json" ||
    backtest.analysis_type!=="RETROSPECTIVE_REVISED_26_1_NOT_ASOF_OR_PROSPECTIVE" ||
    backtest.source_observed_through!==2025 ||
    backtest.model_spec_frozen_2027_unmodified!==true ||
    backtest.historical_source_asof_verified!==false ||
    backtest.prospective_skill_demonstrated!==false ||
    backtest.actual_2027_outcomes_resolved!==0 ||
    backtest.cohort_observations!==2742 ||
    backtest.country_year_positive!==454 ||
    backtest.unique_countries!==196 ||
    JSON.stringify(backtest.years)!==JSON.stringify(
      Array.from({length:14},(_,i)=>i+2012)) ||
    !backtest.caution?.includes("única edición UCDP 26.1") ||
    !backtest.caution?.includes("no existen resultados de 2027"))
    throw Error("Historical 2027-model diagnostic cannot claim verified prospective skill");
  const nearHistorical=(n,target)=>Number.isFinite(n)&&Math.abs(n-target)<1e-10;
  if(!nearHistorical(backtest.primary_brier_model,0.04502180264456287) ||
     !nearHistorical(backtest.primary_brier_global_5y,0.1382851740295057) ||
     !nearHistorical(backtest.secondary_brier_global_markov,0.051519121533228296) ||
     !nearHistorical(backtest.logloss_model,0.17294717580211652) ||
     !nearHistorical(backtest.logloss_global_5y,0.4493836951270839) ||
     !nearHistorical(backtest.logloss_global_markov,0.20554571679333772) ||
     !nearHistorical(backtest.brier_skill_vs_global_5y,
        1-backtest.primary_brier_model/backtest.primary_brier_global_5y) ||
     !nearHistorical(backtest.brier_skill_vs_global_markov,
        1-backtest.primary_brier_model/backtest.secondary_brier_global_markov) ||
     !nearHistorical(backtest.model_expected_calibration_error_bins,0.03200214429534682) ||
     !nearHistorical(backtest.global_markov_expected_calibration_error_bins,0.04805398293657659))
    throw Error("Historical backtest Brier, log-loss or calibration metrics were changed");
  if(!Array.isArray(backtest.annual_results) ||
     backtest.annual_results.length!==14 ||
     backtest.annual_results.some((v,i)=>
       v.year!==i+2012 || !Number.isSafeInteger(v.n)||v.n<175||v.n>196 ||
       !Number.isSafeInteger(v.positives)||v.positives<0||v.positives>v.n||
       ![v.model_brier,v.global_5y_brier,v.global_markov_brier].every(
         x=>Number.isFinite(x)&&x>=0&&x<=1)) ||
     backtest.annual_results.reduce((n,v)=>n+v.n,0)!==2742 ||
     backtest.annual_results.reduce((n,v)=>n+v.positives,0)!==454)
    throw Error("Historical backtest annual cohort or events falsified");
  if(!Array.isArray(backtest.reliability_bins) ||
     backtest.reliability_bins.length!==7 ||
     backtest.reliability_bins.some(v=>!Number.isSafeInteger(v.n)||v.n<0||
       !Number.isFinite(v.lower)||!Number.isFinite(v.upper)||v.lower>=v.upper||
       v.n>0&&(!Number.isFinite(v.predicted)||!Number.isFinite(v.observed)||
           v.predicted<0||v.predicted>1||v.observed<0||v.observed>1)) ||
     backtest.reliability_bins.reduce((n,v)=>n+v.n,0)!==2742)
    throw Error("Historical backtest calibration bins incomplete");
  for(const [key,low,high] of [
    ["exploratory_country_cluster_ci_vs_global_5y",-0.12115165728219118,-0.06744286379252605],
    ["exploratory_country_cluster_ci_vs_markov",-0.009323930713180878,-0.003791108698483742]
  ]){
    const ci=backtest[key];
    if(!Array.isArray(ci)||ci.length!==2||
       !nearHistorical(ci[0],low)||!nearHistorical(ci[1],high))
      throw Error("Historical backtest uncertainty cannot be recast as certified");
  }
  const archival=data.historical_cross_release_statebased;
  const loose=(x,y)=>Number.isFinite(x)&&Math.abs(x-y)<1e-10;
  if(!archival ||
    archival.id!=="EMP-GEO2027-CROSS-RELEASE-231-241-251-261-20261110"||
    archival.linked_question!=="GEO-2027"||
    archival.report_path!=="data/forecast-2027-archival-cross-release.json"||
    archival.model_protocol!=="country_markov_2step_laplace_global_shrink20"||
    archival.status!=="EX_POST_ARCHIVED_VINTAGE_SEPARATED_OUTCOMES_NOT_HISTORICALLY_ISSUED"||
    archival.sample_size!==392||archival.events!==69||
    JSON.stringify(archival.fold_years)!=="[2024,2025]"||
    archival.historical_issue_not_verified!==true||
    archival.dates_independently_notarized!==false||
    archival.forecast_2027_unmodified!==true||
    archival.prospective_results_2027!==0||
    archival.prospective_skill_demonstrated!==false||
    !archival.caution?.includes("ex post")||
    !archival.caution?.includes("196 probabilidades"))
    throw Error("Unverified archival cross-release or false prospective claim");
  const origins=[
    ["23.1",2022,6544,"6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff"],
    ["24.1",2023,6740,"00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260"],
    ["25.1",2024,6936,"564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917"],
    ["26.1",2025,7132,"66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34"]
  ];
  if(!origins.every(([version,year,n,sha])=>
    archival.source_releases?.[version]?.sha256===sha &&
    archival.source_releases[version].last_year===year &&
    archival.source_releases[version].rows===n &&
    archival.source_releases[version].url.startsWith("https://ucdp.uu.se/downloads/organizedviolencecy/")))
    throw Error("Archival cross-release sources or historical cutoff changed");
  const expectedFolds=[
    ["23.1","25.1",2022,2024,196,35],
    ["24.1","26.1",2023,2025,196,34]
  ];
  if(!Array.isArray(archival.folds)||archival.folds.length!==2||
    !expectedFolds.every(([oldv,newv,cutoff,year,n,events],i)=>{
      const f=archival.folds[i];
      return f.origin===oldv&&f.assessment===newv&&f.cutoff===cutoff&&
        f.year===year&&f.observations===n&&f.events===events&&
        [f.model_brier,f.global_markov_brier,f.global_5y_brier].every(x=>Number.isFinite(x)&&x>=0&&x<=1);
    })||
    JSON.stringify(archival.historical_revisions)!==
      JSON.stringify([
        {origin:"23.1",assessment:"25.1",country_years:6544,label_flips:6},
        {origin:"24.1",assessment:"26.1",country_years:6740,label_flips:7}
      ]))
    throw Error("Archival cross-release year coverage or label drift invalid");
  const exactScores=[
    ["model_brier",0.04008405691286656],
    ["global_markov_brier",0.046921116910061844],
    ["global_5y_brier",0.1450678698979093],
    ["model_logloss",0.15439773864360035],
    ["global_markov_logloss",0.19006909182503545],
    ["global_5y_logloss",0.4654125692715784]
  ];
  if(!exactScores.every(([key,value])=>loose(archival[key],value)) ||
     !loose(archival.brier_skill_vs_markov,
        1-archival.model_brier/archival.global_markov_brier) ||
     !loose(archival.brier_skill_vs_global_5y,
        1-archival.model_brier/archival.global_5y_brier)||
     ![archival.bootstrap95_delta_brier_markov,
       archival.bootstrap95_delta_brier_global_5y].every(
       ci=>Array.isArray(ci)&&ci.length===2&&
       ci.every(Number.isFinite)&&ci[0]<ci[1]&&ci[1]<0))
    throw Error("Cross-edition model score cannot be presented as confirmed skill");
  const calib=archival.model_calibration_bins;
  if(!Array.isArray(calib)||calib.length!==7||
     !calib.every(v=>Number.isSafeInteger(v.n)&&v.n>=0&&
       Number.isFinite(v.lower)&&Number.isFinite(v.upper)&&v.upper>v.lower&&
       (v.n===0 ? v.predicted===null&&v.observed===null :
        Number.isFinite(v.predicted)&&Number.isFinite(v.observed)&&
        v.predicted>=0&&v.predicted<=1&&v.observed>=0&&v.observed<=1))||
     calib.reduce((n,v)=>n+v.n,0)!==392||
     !loose(archival.model_bin_ece,0.034583910580885203))
    throw Error("Cross-edition calibration data incomplete or revised");
  const split=data.origin_state_diagnostic_2027;
  if(!split||split.id!=="EMP-GEO2027-ORIGIN-STATE-20261110"||
    split.report_path!=="data/forecast-2027-origin-state-diagnostic.json"||
    split.status!=="POST_HOC_PERSISTENCE_VS_THRESHOLD_ENTRY_ARCHIVED_COUNTRY_VINTAGES"||
    JSON.stringify(split.assessment_years)!=="[2024,2025]"||
    split.observed_country_years!==392||split.positive_threshold_years!==69||
    split.persisted_threshold_positives!==61||split.new_threshold_entries!==8||
    !loose(split.persisted_fraction_of_positives,61/69)||
    split.observation_calendar_steps!==2||
    split.earliest_release_timestamps_verified!==false||
    split.forecast_2027_unchanged!==true||
    split.prospective_2027_outcomes_resolved!==0||
    split.prospective_skill_demonstrated!==false||
    !split.note?.includes("intervalo de bootstrap")||
    !split.note?.includes("NO prueban dos años"))
    throw Error("Cannot present post-hoc origin-state discrimination as prospective onset skill");
  const low=split.prior_below_threshold,high=split.prior_above_threshold;
  if(low?.n!==321||low.events!==8||
     high?.n!==71||high.events!==61||
     !loose(low.event_rate,8/321)||!loose(high.event_rate,61/71)||
     !loose(low.brier_model,0.022647529679559648)||
     !loose(low.brier_global_markov,0.025210281235017312)||
     !loose(high.brier_model,0.1189168067986626)||
     !loose(high.brier_global_markov,0.14507855707469983)||
     !loose(low.brier_skill_model_vs_markov,1-low.brier_model/low.brier_global_markov)||
     !loose(high.brier_skill_model_vs_markov,1-high.brier_model/high.brier_global_markov)||
     !Array.isArray(low.bootstrap_delta_brier_95pct)||
     !Array.isArray(high.bootstrap_delta_brier_95pct)||
     !low.bootstrap_delta_brier_95pct.every(Number.isFinite)||
     !high.bootstrap_delta_brier_95pct.every(Number.isFinite)||
     !(low.bootstrap_delta_brier_95pct[0]<0&&low.bootstrap_delta_brier_95pct[1]>0)||
     !(high.bootstrap_delta_brier_95pct[0]<0&&high.bootstrap_delta_brier_95pct[1]<0))
    throw Error("Conditional origin-state scores and bootstrap conclusions corrupted");
  if(JSON.stringify(split.annual)!==JSON.stringify([
    {year:2024,origin_year:2022,n:196,inactive_to_active:4,active_to_active:31,inactive_to_inactive:155,active_to_inactive:6,model_top_10_hits:10,model_top_20_hits:19,model_top_35_hits:30},
    {year:2025,origin_year:2023,n:196,inactive_to_active:4,active_to_active:30,inactive_to_inactive:158,active_to_inactive:4,model_top_10_hits:9,model_top_20_hits:18,model_top_35_hits:30}
  ]))
    throw Error("Conditional origin-state year-by-year confusion counts changed");
  const entry=data.new_entry_2027_comparison;
  if(!entry || entry.id!=="EMP-GEO2027-THRESHOLD-ENTRY-SPECIFIC-20261110" ||
    entry.report_path!=="data/forecast-2027-entry-comparison.json" ||
    entry.status!=="EXPLORATORY_EX_POST_TWO_TARGET_YEARS_NOT_PROSPECTIVE" ||
    JSON.stringify(entry.target_years)!=="[2024,2025]" ||
    entry.n!==321 || entry.entries!==8 ||
    entry.new_model_tuned_on_outcomes!==false ||
    entry.new_entry_comparator_exploratory_posthoc!==true ||
    entry.prospectively_verified!==false ||
    entry.original_2027_probabilities_unchanged!==true ||
    entry.resolved_2027_forecasts!==0 ||
    !entry.note?.includes("intervalo exploratorio incluye cero") ||
    !entry.note?.includes("no es comienzo de guerra"))
    throw Error("Cannot present post-hoc threshold entry as prospective onset prediction");
  for(const [version,hash,year] of [
    ["23.1","6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff",2022],
    ["24.1","00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260",2023],
    ["25.1","564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917",2024],
    ["26.1","66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34",2025]
  ]){
    const source=entry.source_vintages?.[version];
    if(!source||source.sha256!==hash||source.last_year!==year||
      !source.url.startsWith("https://ucdp.uu.se/downloads/organizedviolencecy/"))
       throw Error("Entry comparator official source fingerprints changed");
  }
  if(![
    ["model_brier",0.022647529679559648],
    ["entry_prior_brier",0.024488096083760312],
    ["global_markov_brier",0.025210281235017312],
    ["model_logloss",0.1002593462099911],
    ["entry_prior_logloss",0.11949284643213998],
    ["global_markov_logloss",0.12748893747625176],
    ["empirical_entry_rate",8/321],
    ["model_predicted_entry_rate",0.042056007016355146],
    ["forecast_over_outcome_ratio",1.6874972815312501]
  ].every(([key,value])=>loose(entry[key],value))||
    !loose(entry.skill_vs_entry_prior,1-entry.model_brier/entry.entry_prior_brier)||
    !loose(entry.skill_vs_global_markov,1-entry.model_brier/entry.global_markov_brier)||
    !Array.isArray(entry.country_bootstrap_95_delta_brier_vs_entry_prior)||
    entry.country_bootstrap_95_delta_brier_vs_entry_prior.length!==2||
    !loose(entry.country_bootstrap_95_delta_brier_vs_entry_prior[0],-0.007279033003436695)||
    !loose(entry.country_bootstrap_95_delta_brier_vs_entry_prior[1],0.0017494189000956107))
    throw Error("Entry comparator Brier, calibration, uncertainty or log-loss falsified");
  if(JSON.stringify(entry.folds)!==JSON.stringify([
    {year:2024,origin_year:2022,n:159,entries:4,
      prior_probability:0.038632412594,
      prior_training_exposures:5175,prior_training_entries:199,
      ap_model:0.2541666666666667,
      roc_auc_model:0.9225806451612903,
      top_5_hits:2,top_10_hits:2,top_20_hits:3},
    {year:2025,origin_year:2023,n:162,entries:4,
      prior_probability:0.038569556263,
      prior_training_exposures:5339,prior_training_entries:205,
      ap_model:0.18091317741206406,
      roc_auc_model:0.814873417721519,
      top_5_hits:1,top_10_hits:1,top_20_hits:1}
  ]))
    throw Error("Entry comparator year-wise classification or training sample changed");
  const onset=data.onset2_homogeneous_vintage;
  if(!onset||onset.id!=="EMP-GEO-ONSET2-231-251-HOMOGENEOUS-20261110"||
    onset.question!=="Q-GEO-01"||
    onset.dataset!=="UCDP Intrastate Country-Level Onset"||
    onset.report_path!=="data/onset2-231-251-homogeneous.json"||
    onset.status!=="EX_POST_HOMOGENEOUS_CROSS_RELEASE_NOT_PROSPECTIVE"||
    onset.origin_year!==2022||
    JSON.stringify(onset.assessed_years)!=="[2023,2024]"||
    onset.country_years!==392||onset.events!==2||
    onset.training_country_years!==4481||onset.training_events!==72||
    onset.model_kind!=="COUNTRY_EMPIRICAL_BAYES_REGULARIZED_RATE_NOT_TWO_STEP_MARKOV"||
    onset.vintage_label_flips!==2||
    onset.vintage_common_country_years!==12161||
    onset.legacy19_excluded!==true||
    onset.asof_historical_release_timestamps_verified!==false||
    onset.historically_issued_forecasts!==false||
    onset.prospective_2027_forecasts_unchanged!==true||
    onset.prospective_2027_results_resolved!==0||
    onset.predictive_skill_demonstrated!==false||
    !onset.warning?.includes("dos positivos")||
    !onset.warning?.includes("No incorporar 19.1")||
    !onset.warning?.includes("No prueba incapacidad universal"))
      throw Error("Unverified homogeneous onset2 study or false prospective claim");
  const onsetSources=[
    ["23.1",2022,"e2cadfa7a87b3949f8c638c27381fbb1b44fb076ccb00570782252d0935a2289"],
    ["25.1",2024,"e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a"],
  ];
  if(!onsetSources.every(([version,lastYear,hash])=>{
    const src=onset.sources?.[version];
    return src?.last_year===lastYear&&src?.sha256===hash&&
      src?.url?.startsWith("https://ucdp.uu.se/downloads/onset/");
  }))throw Error("Homogeneous onset2 source files or hashes changed");
  if(![
    ["model_brier",0.0054337021471445625],
    ["global_brier",0.005201040360443132],
    ["recent_brier",0.005142208533688694],
    ["no_onset_brier",0.00510204081632653],
    ["model_logloss",0.03769405226924217],
    ["global_logloss",0.03734211513950919],
    ["recent_logloss",0.03532320286384879],
    ["training_prob_global",0.016283738567923266],
    ["training_prob_recent_global",0.013238289205702648]
  ].every(([key,value])=>loose(onset[key],value))||
    !loose(onset.brier_skill_global,1-onset.model_brier/onset.global_brier)||
    !loose(onset.brier_skill_recent,1-onset.model_brier/onset.recent_brier)||
    !loose(onset.brier_skill_no_onset,1-onset.model_brier/onset.no_onset_brier))
      throw Error("Homogeneous onset2 negative result was modified");
  if(!Array.isArray(onset.years)||onset.years.length!==2||
    ![
      [2023,196,1,0.005552354259152156,0.00510204081632653,0.358974358974359],
      [2024,196,1,0.005315050035136969,0.019230769230769232,0.8256410256410256]
    ].every(([year,n,events,brier,ap,auc],i)=>{
      const f=onset.years[i];
      return f?.year===year&&f.n===n&&f.events===events&&
        loose(f.model_brier,brier)&&loose(f.ap_model,ap)&&
        loose(f.roc_auc_model,auc)&&
        f.top_5_hits===0&&f.top_10_hits===0&&f.top_20_hits===0;
    }))
      throw Error("Onset2 year-specific ranking or missed onsets concealed");
  if(!Array.isArray(onset.bootstrap_country95_model_minus_global)||
    onset.bootstrap_country95_model_minus_global.length!==2||
    !loose(onset.bootstrap_country95_model_minus_global[0],0.000008119187152832382)||
    !loose(onset.bootstrap_country95_model_minus_global[1],0.00046373996178438316))
      throw Error("Onset2 uncertainty interval changed to imply higher skill");
  return true;
}
export function verifyIssuedForecast2027(document, manifest){
  const e="Invalid frozen GEO-2027 prospective issuance";
  if(!document || !manifest ||
     document.schema!=="idealab.psico.prospective_country_2027.v1" ||
     document.forecast_id!=="PSICO-GEO2027-STATEBASED25-V1" ||
     document.state!=="PREPARED_FOR_PUBLIC_GIT_COMMIT" ||
     manifest.schema!=="idealab.psico.prospective_issue_manifest.v1" ||
     manifest.forecast_id!==document.forecast_id ||
     manifest.status!=="ISSUED_PROSPECTIVE_UNRESOLVED" ||
     manifest.question!=="Q-GEO-2027-01" ||
     manifest.target_year!==2027 || manifest.issued_country_count!==196 ||
     manifest.outcomes_resolved!==0 || manifest.demonstrated_predictive_skill!==false ||
     manifest.independently_notarized!==false ||
     manifest.forecast_path!=="data/forecast-2027-ucdp261.json" ||
     manifest.forecast_sha256!=="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5" ||
     manifest.preregistered_protocol_main_commit!=="87959a117e1b30323392a488c48c9afb1cb0bffc" ||
     manifest.first_public_forecast_commit!=="3bb3561c8d6182c30624591276c705fb76ce99dc" ||
     manifest.first_public_forecast_commit_utc!=="2026-11-10T17:23:12Z" ||
     manifest.canonical_document_commit!=="8b924e0b0c7a07e27977160c9658cfed77940aff" ||
     manifest.canonical_document_commit_utc!=="2026-11-10T17:32:54Z" ||
     manifest.canonical_document_status!=="BYTE_IDENTICAL_TO_FROZEN_GENERATOR_OUTPUT" ||
     !(manifest.first_public_forecast_commit_utc<manifest.canonical_document_commit_utc) ||
     manifest.preregistered_at_utc!=="2026-11-10T17:20:43Z" ||
     !(manifest.preregistered_at_utc<manifest.first_public_forecast_commit_utc) ||
     !(manifest.first_public_forecast_commit_utc<"2027-01-01T00:00:00Z") ||
     manifest.time_provenance!=="PUBLIC_GITHUB_COMMIT_METADATA_NOT_INDEPENDENT_TIMESTAMP_NOTARY" ||
     manifest.source_zip_sha256!=="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34" ||
     manifest.observed_data_through!==2025 ||
     manifest.resolution_status!=="PENDING_FIRST_OFFICIAL_UCDP_YEAR_2027_RELEASE")
    throw Error(e);
  const s=document.source,t=document.target,p=document.protocol,a=document.training_summary;
  if(s?.dataset!=="UCDP OrganizedViolenceCY" || s.version!=="26.1" ||
     s.sha256!==manifest.source_zip_sha256 ||
     s.url!=="https://ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-261-csv.zip" ||
     s.license!=="CC BY 4.0" || s.records_in_edition!==7132 ||
     s.data_last_year!==2025 ||
     t?.year!==2027 || t.source_field!=="sb_total_deaths_best" ||
     t.binary_rule!=="1 iff UCDP official 2027 country-year sb_total_deaths_best >= 25; otherwise 0" ||
     t.not_onset2!==true ||
     t.not_state_violence_against_civilians!==true ||
     !t.missing_policy?.includes("never assumed 0") ||
     p?.horizon_years!==2 || p.training_last_year!==2025 ||
     p.model_primary!=="country_markov_2step_laplace_global_shrink20" ||
     p.baseline_primary!=="global_laplace_5y_2021_2025" ||
     p.secondary_comparator!=="global_markov_2step_laplace" ||
     p.skill_not_demonstrated!==true ||
     p.primary_loss!=="Brier score of frozen p_model minus frozen p_baseline_global_5y over resolved cohort" ||
     document.provenance?.independent_timestamp_authority!==false ||
     document.provenance?.historical_forecasts_issued!==false ||
     !/^[a-f0-9]{64}$/.test(document.provenance?.generator_sha256||"") ||
     a?.cohort_n!==196 || a.global_5y_exposures!==980 ||
     a.global_5y_positive!==172 ||
     !Number.isFinite(a.baseline_global_5y) ||
     !Array.isArray(document.countries) || document.countries.length!==196)
    throw Error(e);
  let prev=0;
  for(const row of document.countries){
    if(!Number.isSafeInteger(row.country_id)||row.country_id<=prev||
       typeof row.country!=="string"||!row.country||row.country.length>150||
       ![0,1].includes(row.last_observed_state_2025) ||
       !["p_model","p_global_markov","p_baseline_global_5y"].every(key=>
          Number.isFinite(row[key])&&row[key]>0&&row[key]<1) ||
       row.p_baseline_global_5y!==a.baseline_global_5y)
      throw Error(e);
    prev=row.country_id;
  }
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
