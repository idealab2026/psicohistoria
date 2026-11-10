import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {verifyResearch,verifyIssuedForecast2027,parseForecastCSV,evaluateLocalForecast,CSV_TEMPLATE} from "../src/research.mjs";

const registry=JSON.parse(readFileSync(new URL("../data/research.json",import.meta.url),"utf8"));
test("the institutional research registry is complete and does not claim forecasting skill",()=>{
 assert.equal(verifyResearch(registry),true);
 assert.equal(registry.programs.length,7);
 assert.ok(registry.programs.every(p=>p.skill_demonstrated===false));
});
test("unknown source domains are rejected",()=>{
 const changed=structuredClone(registry);changed.programs[0].source.url="https://example.com/source";
 assert.throws(()=>verifyResearch(changed),/allowlist/);
});
test("prematurely issued forecasts are rejected",()=>{
 const changed=structuredClone(registry);changed.forecast_issued=2;
 assert.throws(()=>verifyResearch(changed),/Invalid issued/);
});
test("the local Brier score is correct and not verified",()=>{
 const result=evaluateLocalForecast(parseForecastCSV(CSV_TEMPLATE));
 assert.equal(result.n,2);
 assert.ok(Math.abs(result.model_brier-0.065)<1e-12);
 assert.equal(result.baseline_brier,0.25);
 assert.equal(result.verified_independently,false);
});
test("lookahead and forecasts after event start are rejected",()=>{
 const rows=parseForecastCSV(CSV_TEMPLATE);rows[0].issued_at="2024-04-01";
 assert.throws(()=>evaluateLocalForecast(rows),/Temporal/);
});
test("malformed numeric and temporal rows fail closed",()=>{
 let rows=parseForecastCSV(CSV_TEMPLATE);rows[0].model_probability="1.4";
 assert.throws(()=>evaluateLocalForecast(rows),/probability/);
 rows=parseForecastCSV(CSV_TEMPLATE);rows[0].event_end="2024-02-30";
 assert.throws(()=>evaluateLocalForecast(rows),/calendar/);
 assert.throws(()=>parseForecastCSV("a,b,c\n1,2,3"),/columns/);
});
test("formulas, text and unvalidated scientific evidence are not accepted as probabilities",()=>{
 const rows=parseForecastCSV(CSV_TEMPLATE); rows[0].model_probability="=1+0";
 assert.throws(()=>evaluateLocalForecast(rows));
});


test("priority research questions have decision-value protocols and no claimed predictive skill",()=>{
 assert.equal(registry.questions.length,10);
 assert.deepEqual(registry.questions.reduce((counts,q)=>(counts[q.priority]=(counts[q.priority]||0)+1,counts),{}),{P1:3,P2:5,P3:2});
 assert.ok(registry.questions.every(q=>q.skill_demonstrated===false));
 assert.ok(registry.questions.every(q=>q.target&&q.horizon&&q.baseline&&q.decision&&q.gate));
 const legacy=registry.questions.find(q=>q.id==="Q-GEO-02");
 assert.equal(legacy.model_status,"retrospectivo_no_prospectivo");
});
test("agenda rejects missing baselines, unsupported priorities or fabricated success",()=>{
 let changed=structuredClone(registry);
 changed.questions[0].baseline="";
 assert.throws(()=>verifyResearch(changed),/protocol/);
 changed=structuredClone(registry);
 changed.questions[1].skill_demonstrated=true;
 assert.throws(()=>verifyResearch(changed),/Premature/);
 changed=structuredClone(registry);
 changed.questions[2].priority="P0";
 assert.throws(()=>verifyResearch(changed),/priority/);
 changed=structuredClone(registry);
 changed.questions[3].program="BAD-01";
 assert.throws(()=>verifyResearch(changed),/orphan/);
});
test("question agenda is visible as an institutional research view",()=>{
 const source=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(source,/\["questions","Preguntas útiles"\]/);
 assert.match(source,/function renderUsefulQuestions\(/);
 assert.match(source,/case "question-priority"/);
 assert.match(source,/¿Qué queremos anticipar/);
 assert.match(source,/Sin validar/);
});

test("real UCDP empirical study is reproducible and explicitly NOT prospective",()=>{
 const empirical=registry.empirical_studies[0];
 assert.equal(empirical.source_sha256,"e2b59e65aaca88403991465b78fb407d7eddcefadeb18c7f1397bfe2ea83fe6a");
 assert.equal(empirical.observations,2939);
 assert.equal(empirical.positive_events,41);
 assert.ok(empirical.brier_country<empirical.brier_global);
 assert.ok(empirical.delta_brier_confidence_interval[0]<0);
 assert.ok(empirical.delta_brier_confidence_interval[1]>0);
 assert.equal(empirical.prospective_validation,false);
 assert.equal(empirical.source_point_in_time_verified,false);
 assert.equal(empirical.more_reliable_than_baseline_demonstrated,false);
 assert.equal(verifyResearch(registry),true);
});
test("research UI separates real retrospective source from synthetic software samples",()=>{
 const source=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(source,/function renderEmpiricalEvidence/);
 assert.match(source,/renderEmpiricalEvidence\(\)\+section/);
 assert.match(source,/no hay superioridad robusta demostrada/);
 assert.match(source,/La tabla siguiente usa muestras inventadas/);
});
test("fabricated prospective achievement and invalid empirical scores are rejected",()=>{
 let x=structuredClone(registry);x.empirical_studies[0].prospective_validation=true;
 assert.throws(()=>verifyResearch(x),/cannot be displayed/);
 x=structuredClone(registry);x.empirical_studies[0].more_reliable_than_baseline_demonstrated=true;
 assert.throws(()=>verifyResearch(x),/cannot be displayed/);
 x=structuredClone(registry);x.empirical_studies[0].brier_global=NaN;
 assert.throws(()=>verifyResearch(x),/empirical score/);
 x=structuredClone(registry);x.empirical_studies[0].source_sha256="f";
 assert.throws(()=>verifyResearch(x),/provenance/);
 x=structuredClone(registry);x.empirical_studies[0].delta_brier_confidence_interval=[1,0];
 assert.throws(()=>verifyResearch(x),/confidence interval/);
});

test("conditional risk-set benchmark uses two authentic UCDP 25.1 sources and exploratory labels",()=>{
 const r=registry.riskset_study;
 assert.equal(r.scenarios.length,2);
 assert.deepEqual(r.scenarios.map(x=>x.observations),[2465,2404]);
 assert.deepEqual(r.scenarios.map(x=>x.events),[40,40]);
 assert.ok(r.scenarios.every(x=>x.brier_model<x.brier_baseline));
 assert.ok(r.scenarios.every(x=>x.cluster_delta_interval[0]<0&&x.cluster_delta_interval[1]<0));
 assert.equal(r.point_in_time_verified,false);
 assert.equal(r.prospective_forecasts_issued,0);
 assert.equal(r.operational_utility_demonstrated,false);
 assert.equal(r.exploratory_confidence_intervals,true);
 assert.ok(verifyResearch(registry));
});
test("falsified vintages, utility claims and inconsistent scoring are prohibited",()=>{
 let r=structuredClone(registry);
 r.riskset_study.point_in_time_verified=true;
 assert.throws(()=>verifyResearch(r),/provenance|retrospective/i);
 r=structuredClone(registry);
 r.riskset_study.operational_utility_demonstrated=true;
 assert.throws(()=>verifyResearch(r),/provenance|retrospective/i);
 r=structuredClone(registry);
 r.riskset_study.sources[1].sha256="bad";
 assert.throws(()=>verifyResearch(r),/provenance/i);
 r=structuredClone(registry);
 r.riskset_study.scenarios[0].relative_brier_improvement=0.999;
 assert.throws(()=>verifyResearch(r),/inconsistent/);
});
test("new actual study remains separate from retrospective all-year and synthetic evaluator",()=>{
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(site,/function renderConditionalRisksetEvidence\(/);
 assert.match(site,/renderConditionalRisksetEvidence\(\)\+renderEmpiricalEvidence\(\)/);
 assert.match(site,/no acredita predicción futura/);
 assert.match(site,/La tabla siguiente usa muestras inventadas/);
});

test("historical temporal and prior sensitivity studies remain exploratory",()=>{
 const d=registry.riskset_study.temporal_robustness;
 assert.equal(d.periods.length,4);
 assert.deepEqual(d.periods.map(x=>x.events),[26,14,26,14]);
 assert.equal(d.priors.length,6);
 assert.equal(d.independent_confirmation,false);
 assert.equal(d.retrospective_point_in_time_verified,false);
 assert.ok(d.periods.every(x=>x.relative_brier_improvement>0));
 assert.ok(verifyResearch(registry));
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(site,/¿Es estable el resultado entre periodos/);
 assert.match(site,/study\.temporal_robustness\.note/);
});
test("robustness evidence cannot be declared independent confirmation or altered after source",()=>{
 let r=structuredClone(registry);
 r.riskset_study.temporal_robustness.independent_confirmation=true;
 assert.throws(()=>verifyResearch(r),/Temporal stability/);
 r=structuredClone(registry);
 r.riskset_study.temporal_robustness.priors[1].relative_brier_improvement=0.9;
 assert.throws(()=>verifyResearch(r),/Sensitivity does not reproduce/);
 r=structuredClone(registry);
 r.riskset_study.temporal_robustness.periods[1].confidence_delta_brier=[NaN,1];
 assert.throws(()=>verifyResearch(r),/Temporal stability score/);
});

test("one-event historical holdout is negative for Brier and cannot establish skill",()=>{
 const v=registry.historical_vintage_2024;
 assert.equal(v.sample_size,160);
 assert.equal(v.positives,1);
 assert.equal(v.training_last_year,2022);
 assert.equal(v.year,2024);
 assert.ok(v.brier_model>v.brier_global);
 assert.ok(v.logloss_model<v.logloss_global);
 assert.ok((1-v.logloss_model/v.logloss_global)>0.13);
 assert.ok(v.relative_brier_skill<0);
 assert.ok(v.uncertainty_brier_delta[0]<0&&v.uncertainty_brier_delta[1]>0);
 assert.equal(v.model_issued_before_event,false);
 assert.equal(v.prospective_skill_demonstrated,false);
 assert.equal(v.too_few_events_for_skill_inference,true);
 assert.equal(verifyResearch(registry),true);
});
test("real archival source and negative score are fail-closed",()=>{
 let v=structuredClone(registry);
 v.historical_vintage_2024.model_issued_before_event=true;
 assert.throws(()=>verifyResearch(v),/archived vintage/);
 v=structuredClone(registry);
 v.historical_vintage_2024.sources[0].sha256="bogus";
 assert.throws(()=>verifyResearch(v),/archived vintage/);
 v=structuredClone(registry);
 v.historical_vintage_2024.relative_brier_skill=1;
 assert.throws(()=>verifyResearch(v),/negative or uncertain/);
 v=structuredClone(registry);
 v.historical_vintage_2024.brier_model=0;
 assert.throws(()=>verifyResearch(v),/negative or uncertain/);
 v=structuredClone(registry);
 v.historical_vintage_2024.logloss_model=0.99;
 assert.throws(()=>verifyResearch(v),/log-loss disagreement/);
});
test("website leads with source-backed negative holdout rather than a synthetic prediction",()=>{
 const source=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(source,/function renderVintageHoldout/);
 assert.match(source,/renderRecencySensitivity\(\)\+renderExternalVintageHoldout\(\)\+renderVintageHoldout\(\)\+renderHistoricalLabelRevisions\(\)\+renderConditionalRisksetEvidence\(\)/);
 assert.match(source,/No concluyente/);
 assert.match(source,/Valor negativo/);
 assert.match(source,/Discrepancia de pérdidas/);
 assert.match(source,/log-loss mejora/);
 assert.match(source,/no se emitió ninguna predicción en 2024/);
});

test("cross-release onset2 historical drift is recorded without prospective claims",()=>{
 const r=registry.historical_label_revisions;
 assert.equal(r.observations,12161);
 assert.equal(r.labels_flipped,2);
 assert.equal(r.flips_zero_to_one,1);
 assert.equal(r.flips_one_to_zero,1);
 assert.equal(r.positives_23_1,242);
 assert.equal(r.positives_25_1,242);
 assert.deepEqual(r.changes_by_year.map(x=>x.year),[2018,2021]);
 assert.equal(r.prospective_skill_demonstrated,false);
 assert.equal(verifyResearch(registry),true);
 const site=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(site,/function renderHistoricalLabelRevisions/);
 assert.match(site,/Revisiones de etiquetas|ETIQUETAS REVISADAS/);
});

test("historical revision score and event counts cannot be falsely changed",()=>{
 let x=structuredClone(registry);
 x.historical_label_revisions.labels_flipped=0;
 assert.throws(()=>verifyResearch(x),/historical onset revision/);
 x=structuredClone(registry);
 x.historical_label_revisions.prospective_skill_demonstrated=true;
 assert.throws(()=>verifyResearch(x),/historical onset revision/);
 x=structuredClone(registry);
 x.historical_label_revisions.source_sha256s[0]="f".repeat(64);
 assert.throws(()=>verifyResearch(x),/historical onset revision/);
});

test("multiple genuine UCDP vintages expose a negative Brier score in 715 country-years",()=>{
 const e=registry.external_vintage_holdout;
 assert.equal(e.aggregate.country_years,715);
 assert.equal(e.aggregate.events,7);
 assert.ok(e.aggregate.brier_model>e.aggregate.brier_global);
 assert.ok(e.aggregate.logloss_model>e.aggregate.logloss_global);
 assert.ok(e.aggregate.brier_global>e.aggregate.brier_no_event);
 assert.ok(e.aggregate.relative_brier_skill_global<0);
 assert.deepEqual(e.studies.flatMap(s=>s.years.map(x=>x.year)),[2020,2021,2022,2024]);
 assert.equal(e.sources["19.1"].last_year,2017);
 assert.equal(e.legacy_19_1_duplicates.duplicate_country_year_keys,47);
 assert.equal(e.legacy_19_1_duplicates.contradictory_onset2_keys,13);
 assert.equal(e.legacy_19_1_duplicates.choice_made_after_data_diagnostics,true);
 assert.equal(e.point_in_time_verified,false);
 assert.equal(e.prospective_predictions_issued,0);
 assert.equal(e.operational_utility_demonstrated,false);
 assert.equal(verifyResearch(registry),true);
 const html=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(html,/function renderExternalVintageHoldout/);
 assert.match(html,/no se emitieron predicciones en esos años/i);
 assert.match(html,/peor Brier y peor log-loss/);
});
test("do not allow fabricated success, missing source, or changed events in archived evaluation",()=>{
 let e=structuredClone(registry);
 e.external_vintage_holdout.more_reliable_than_global_demonstrated=true;
 assert.throws(()=>verifyResearch(e),/Unverified cross-release/);
 e=structuredClone(registry);
 e.external_vintage_holdout.aggregate.brier_model=0.001;
 assert.throws(()=>verifyResearch(e),/Cross-release negative score/);
 e=structuredClone(registry);
 e.external_vintage_holdout.sources["19.1"].last_year=2018;
 assert.throws(()=>verifyResearch(e),/source hash or cutoff/);
 e=structuredClone(registry);
 e.external_vintage_holdout.studies[0].years[2].events=99;
 assert.throws(()=>verifyResearch(e),/target years and events/);
 e=structuredClone(registry);
 e.external_vintage_holdout.legacy_19_1_duplicates.contradictory_onset2_keys=0;
 assert.throws(()=>verifyResearch(e),/Unverified cross-release/);
});

test("consistent UCDP country-level recency experiment is cautious about post-hoc selection",()=>{
 const r=registry.recency_sensitivity_study;
 assert.deepEqual(r.source_vintages,["23.1","25.1"]);
 assert.deepEqual(r.windows_years,[5,10,20]);
 assert.equal(r.status,"EXPLORATORY_POSTHOC_NOT_PROSPECTIVE");
 assert.equal(r.internally_revised_vintage.n,1568);
 assert.equal(r.internally_revised_vintage.events,22);
 assert.equal(r.cross_release_holdout_2024.n,196);
 assert.equal(r.cross_release_holdout_2024.events,1);
 assert.ok(r.cross_release_holdout_2024.metrics.global_5.brier <
           r.cross_release_holdout_2024.metrics.global_full.brier);
 assert.ok(r.cross_release_holdout_2024.metrics.country_5.brier >
           r.cross_release_holdout_2024.metrics.global_5.brier);
 assert.equal(r.legacy_19_1_excluded_due_to_country_year_unit_mismatch,true);
 assert.equal(r.new_independent_confirmatory_holdout,false);
 assert.equal(r.prospective_forecasts_issued,0);
 assert.ok(verifyResearch(registry));
 const html=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(html,/function renderRecencySensitivity/);
 assert.match(html,/Cuadrícula completa de ocho modelos/);
 assert.match(html,/backtest homogéneo validado/);
});

test("recency and vintage compatibility safeguards reject rewritten study metadata",()=>{
 let r=structuredClone(registry);
 r.recency_sensitivity_study.skill_demonstrated=true;
 assert.throws(()=>verifyResearch(r),/Recency experiment/);
 r=structuredClone(registry);
 r.recency_sensitivity_study.legacy_19_1_excluded_due_to_country_year_unit_mismatch=false;
 assert.throws(()=>verifyResearch(r),/Recency experiment/);
 r=structuredClone(registry);
 r.recency_sensitivity_study.cross_release_holdout_2024.metrics.global_5.brier=0.99;
 assert.throws(()=>verifyResearch(r),/Recency sensitivity/);
 r=structuredClone(registry);
 r.recency_sensitivity_study.source_sha256["23.1"]="f".repeat(64);
 assert.throws(()=>verifyResearch(r),/Recency experiment/);
});

test("a frozen 196-country 2027 issue is publicly committed after its preregistration",()=>{
 const raw=readFileSync(new URL("../data/forecast-2027-ucdp261.json",import.meta.url),"utf8");
 const forecast=JSON.parse(raw);
 const manifest=JSON.parse(readFileSync(new URL("../data/forecast-2027-manifest.json",import.meta.url),"utf8"));
 assert.equal(createHash("sha256").update(raw,"utf8").digest("hex"),manifest.forecast_sha256);
 assert.equal(verifyIssuedForecast2027(forecast,manifest),true);
 assert.equal(registry.forecast_issued,1);
 assert.equal(registry.prospective_results_verified,0);
 assert.equal(registry.prospective_2027_issue.countries_issued,196);
 assert.equal(registry.prospective_2027_issue.outcomes_resolved,0);
 assert.equal(registry.prospective_2027_issue.first_public_forecast_commit,manifest.first_public_forecast_commit);
 assert.equal(forecast.target.not_onset2,true);
 assert.equal(forecast.source.data_last_year,2025);
 assert.ok(manifest.preregistered_at_utc<manifest.first_public_forecast_commit_utc);
 assert.ok(manifest.first_public_forecast_commit_utc<"2027-01-01T00:00:00Z");
});

test("2027 issue refuses to claim independently verified outcomes or valid skill",()=>{
 const f=JSON.parse(readFileSync(new URL("../data/forecast-2027-ucdp261.json",import.meta.url),"utf8"));
 const m=JSON.parse(readFileSync(new URL("../data/forecast-2027-manifest.json",import.meta.url),"utf8"));
 let mutated={...m,outcomes_resolved:1};
 assert.throws(()=>verifyIssuedForecast2027(f,mutated),/Invalid frozen GEO-2027/);
 mutated={...m,demonstrated_predictive_skill:true};
 assert.throws(()=>verifyIssuedForecast2027(f,mutated),/Invalid frozen GEO-2027/);
 mutated={...m,first_public_forecast_commit_utc:"2027-02-01T00:00:00Z"};
 assert.throws(()=>verifyIssuedForecast2027(f,mutated),/Invalid frozen GEO-2027/);
 mutated=structuredClone(f);mutated.countries[0].p_model=1.2;
 assert.throws(()=>verifyIssuedForecast2027(mutated,m),/Invalid frozen GEO-2027/);
 mutated=structuredClone(f);mutated.countries[1].country_id=mutated.countries[0].country_id;
 assert.throws(()=>verifyIssuedForecast2027(mutated,m),/Invalid frozen GEO-2027/);
 mutated=structuredClone(f);mutated.source.data_last_year=2026;
 assert.throws(()=>verifyIssuedForecast2027(mutated,m),/Invalid frozen GEO-2027/);
 const mutatedRegistry=structuredClone(registry);
 mutatedRegistry.prospective_2027_issue.skill_demonstrated=true;
 assert.throws(()=>verifyResearch(mutatedRegistry),/Unverified or mutated GEO-2027/);
});

test("reproducibility audit is public, purely pre-outcome, and concordant with the frozen issue",()=>{
 const audit=JSON.parse(readFileSync(new URL("../data/forecast-2027-audit.json",import.meta.url),"utf8"));
 const forecast=JSON.parse(readFileSync(new URL("../data/forecast-2027-ucdp261.json",import.meta.url),"utf8"));
 assert.equal(audit.schema,"idealab.psico.forecast_2027_frozen_audit.v1");
 assert.equal(audit.countries,196);
 assert.equal(audit.resolution_count,0);
 assert.equal(audit.forecast_skill_demonstrated,false);
 assert.equal(audit.forecast_file_sha256,"5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5");
 assert.equal(audit.active_state_countries_in_2025,34);
 assert.equal(audit.inactive_state_countries_in_2025,162);
 assert.equal(audit.distinct_model_probabilities,73);
 assert.equal(audit.model_histogram.reduce((n,v)=>n+v.countries,0),196);
 assert.equal(audit.model_expected_positive_countries,Number(
     forecast.countries.reduce((a,r)=>a+r.p_model,0).toFixed(9)));
 assert.equal(audit.global_5y_expected_positive_countries,Number(
     forecast.countries.reduce((a,r)=>a+r.p_baseline_global_5y,0).toFixed(9)));
 assert.match(audit.not_an_outcome,/not actual 2027 conflict outcomes/);
 const ui=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(ui,/Distribución y control de probabilidades/);
 assert.match(ui,/data\/forecast-2027-audit\.json/);
});

test("same frozen 2027 model improves retrospectively and preserves the 2027 issue",()=>{
 const r=registry.statebased_2027_spec_backtest;
 const source=JSON.parse(readFileSync(new URL("../data/forecast-2027-historical-backtest.json",import.meta.url),"utf8"));
 assert.equal(source.schema,"idealab.psico.statebased_two_year_backtest.v1");
 assert.equal(source.analysis_type,"RETROSPECTIVE_REVISED_26_1_NOT_ASOF_OR_PROSPECTIVE");
 assert.equal(source.source.sha256,r.source_sha256);
 assert.equal(source.country_years,2742);
 assert.equal(source.positive_events,454);
 assert.equal(r.actual_2027_outcomes_resolved,0);
 assert.equal(source.prospective_2027_outcomes_resolved,0);
 assert.equal(r.prospective_skill_demonstrated,false);
 assert.equal(r.historical_source_asof_verified,false);
 assert.equal(source.target_years.length,14);
 assert.equal(source.cohorts_by_year.length,14);
 assert.deepEqual(r.years,source.target_years);
 assert.equal(r.annual_results.reduce((n,x)=>n+x.n,0),source.country_years);
 assert.equal(r.annual_results.reduce((n,x)=>n+x.positives,0),source.positive_events);
 assert.ok(r.primary_brier_model<r.secondary_brier_global_markov);
 assert.ok(r.primary_brier_model<r.primary_brier_global_5y);
 assert.equal(r.primary_brier_model,source.pooled_scores.p_model.brier);
 assert.equal(r.primary_brier_global_5y,source.pooled_scores.p_baseline_global_5y.brier);
 assert.equal(r.secondary_brier_global_markov,source.pooled_scores.p_global_markov.brier);
 assert.equal(r.reliability_bins.reduce((n,v)=>n+v.n,0),source.country_years);
 assert.equal(r.unique_countries,196);
 assert.equal(verifyResearch(registry),true);
 const ui=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(ui,/function renderStatebasedHistoricalBacktest/);
 assert.match(ui,/Reproducción del mismo modelo de horizonte dos años/);
 assert.match(ui,/no se han modificado/);
});
test("historical study cannot falsify scores or be represented as skill demonstrated",()=>{
 let changed=structuredClone(registry);
 changed.statebased_2027_spec_backtest.prospective_skill_demonstrated=true;
 assert.throws(()=>verifyResearch(changed),/Historical 2027-model diagnostic/);
 changed=structuredClone(registry);
 changed.statebased_2027_spec_backtest.primary_brier_model=0.001;
 assert.throws(()=>verifyResearch(changed),/Historical backtest Brier/);
 changed=structuredClone(registry);
 changed.statebased_2027_spec_backtest.historical_source_asof_verified=true;
 assert.throws(()=>verifyResearch(changed),/Historical 2027-model diagnostic/);
 changed=structuredClone(registry);
 changed.statebased_2027_spec_backtest.annual_results[0].positives=99;
 assert.throws(()=>verifyResearch(changed),/Historical backtest annual/);
 changed=structuredClone(registry);
 changed.statebased_2027_spec_backtest.reliability_bins[0].n=0;
 assert.throws(()=>verifyResearch(changed),/Historical backtest calibration/);
});

test("GEO-2027 source-separated historical holdouts use real archived versions without forecast issuance claims",()=>{
 const r=registry.historical_cross_release_statebased;
 const report=JSON.parse(readFileSync(new URL("../data/forecast-2027-archival-cross-release.json",import.meta.url),"utf8"));
 assert.equal(report.schema,"idealab.psico.statebased_archival_cross_release_v1");
 assert.equal(r.sample_size,392);
 assert.equal(r.events,69);
 assert.deepEqual(r.fold_years,[2024,2025]);
 assert.deepEqual(r.folds.map(x=>[x.origin,x.assessment,x.cutoff,x.year,x.observations,x.events]),
 [[ "23.1","25.1",2022,2024,196,35 ],[ "24.1","26.1",2023,2025,196,34 ]]);
 assert.deepEqual(r.historical_revisions.map(x=>x.label_flips),[6,7]);
 assert.deepEqual(r.historical_revisions.map(x=>x.country_years),[6544,6740]);
 assert.deepEqual(Object.keys(r.source_releases),["23.1","24.1","25.1","26.1"]);
 assert.deepEqual(report.sources["23.1"].last_year,2022);
 assert.equal(report.sources["23.1"].format,"XLSX");
 assert.equal(report.country_years,r.sample_size);
 assert.equal(r.model_calibration_bins.reduce((n,x)=>n+x.n,0),392);
 assert.ok(r.model_bin_ece>0.03&&r.model_bin_ece<0.04);
 assert.equal(report.positives,r.events);
 assert.equal(report.metrics.p_model.brier,r.model_brier);
 assert.equal(report.metrics.p_global_markov.brier,r.global_markov_brier);
 assert.equal(report.metrics.p_baseline_global_5y.brier,r.global_5y_brier);
 assert.ok(r.model_brier<r.global_markov_brier);
 assert.ok(r.global_markov_brier<r.global_5y_brier);
 assert.equal(r.historical_issue_not_verified,true);
 assert.equal(r.dates_independently_notarized,false);
 assert.equal(r.forecast_2027_unmodified,true);
 assert.equal(r.prospective_results_2027,0);
 assert.equal(r.prospective_skill_demonstrated,false);
 assert.equal(report.prospective_2027_outcomes_resolved,0);
 assert.equal(verifyResearch(registry),true);
 const source=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(source,/function renderArchivalCrossRelease/);
 assert.match(source,/reconstrucción ex post/i);
 assert.match(source,/ediciones oficiales diferentes/i);
 assert.match(source,/Calibración retrospectiva entre ediciones/);
});

test("historical release and score integrity cannot be fabricated or relabeled prospective",()=>{
 let d=structuredClone(registry);
 d.historical_cross_release_statebased.prospective_skill_demonstrated=true;
 assert.throws(()=>verifyResearch(d),/Unverified archival cross-release/);
 d=structuredClone(registry);
 d.historical_cross_release_statebased.source_releases["24.1"].sha256="f".repeat(64);
 assert.throws(()=>verifyResearch(d),/Archival cross-release sources/);
 d=structuredClone(registry);
 d.historical_cross_release_statebased.folds[0].events=0;
 assert.throws(()=>verifyResearch(d),/Archival cross-release year coverage/);
 d=structuredClone(registry);
 d.historical_cross_release_statebased.model_brier=0.001;
 assert.throws(()=>verifyResearch(d),/Cross-edition model score/);
 d=structuredClone(registry);
 d.historical_cross_release_statebased.historical_revisions[0].label_flips=0;
 assert.throws(()=>verifyResearch(d),/Archival cross-release year coverage/);
 d=structuredClone(registry);
 d.historical_cross_release_statebased.model_calibration_bins[0].n=0;
 assert.throws(()=>verifyResearch(d),/Cross-edition calibration/);
});

test("GEO-2027 historical Markov advantage is mostly persistence, not new wars",()=>{
 const x=registry.origin_state_diagnostic_2027;
 const report=JSON.parse(readFileSync(new URL("../data/forecast-2027-origin-state-diagnostic.json",import.meta.url),"utf8"));
 assert.equal(report.schema,"idealab.psico.geo2027_origin_state_skill_diagnostic.v1");
 assert.equal(report.study_type,x.status);
 assert.equal(report.pooled_total,392);
 assert.equal(report.pooled_positive,69);
 assert.equal(x.persisted_threshold_positives,61);
 assert.equal(x.new_threshold_entries,8);
 assert.equal(x.prior_below_threshold.n,321);
 assert.equal(x.prior_above_threshold.n,71);
 assert.equal(x.prior_below_threshold.events,8);
 assert.equal(x.prior_above_threshold.events,61);
 assert.equal(x.prior_below_threshold.n+x.prior_above_threshold.n,392);
 assert.equal(x.prior_below_threshold.events+x.prior_above_threshold.events,69);
 assert.equal(report.conditional_groups.BELOW_25_AT_ORIGIN.positive_threshold_outcomes,8);
 assert.ok(x.prior_below_threshold.bootstrap_delta_brier_95pct[0]<0);
 assert.ok(x.prior_below_threshold.bootstrap_delta_brier_95pct[1]>0);
 assert.ok(x.prior_above_threshold.bootstrap_delta_brier_95pct[1]<0);
 assert.equal(x.prospective_2027_outcomes_resolved,0);
 assert.equal(x.prospective_skill_demonstrated,false);
 assert.equal(x.forecast_2027_unchanged,true);
 assert.equal(x.earliest_release_timestamps_verified,false);
 assert.equal(verifyResearch(registry),true);
 const ui=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(ui,/function renderOriginStateSkill/);
 assert.match(ui,/no demuestra detección de nuevas guerras/);
 assert.match(ui,/incluye cero/);
});
test("origin-state diagnostics reject invented threshold entries and prospective skill",()=>{
 let d=structuredClone(registry);
 d.origin_state_diagnostic_2027.new_threshold_entries=0;
 assert.throws(()=>verifyResearch(d),/Cannot present post-hoc origin-state/);
 d=structuredClone(registry);
 d.origin_state_diagnostic_2027.prior_below_threshold.bootstrap_delta_brier_95pct[1]=-0.0001;
 assert.throws(()=>verifyResearch(d),/Conditional origin-state scores/);
 d=structuredClone(registry);
 d.origin_state_diagnostic_2027.prior_above_threshold.events=30;
 assert.throws(()=>verifyResearch(d),/Conditional origin-state scores/);
 d=structuredClone(registry);
 d.origin_state_diagnostic_2027.prospective_skill_demonstrated=true;
 assert.throws(()=>verifyResearch(d),/Cannot present post-hoc origin-state/);
 d=structuredClone(registry);
 d.origin_state_diagnostic_2027.annual[1].inactive_to_active=8;
 assert.throws(()=>verifyResearch(d),/Conditional origin-state year-by-year/);
});

test("only initially-inactive countries enter threshold-entry evaluation; baseline fits earlier source",()=>{
 const x=registry.new_entry_2027_comparison;
 const report=JSON.parse(readFileSync(new URL("../data/forecast-2027-entry-comparison.json",import.meta.url),"utf8"));
 assert.equal(x.id,"EMP-GEO2027-THRESHOLD-ENTRY-SPECIFIC-20261110");
 assert.equal(x.status,"EXPLORATORY_EX_POST_TWO_TARGET_YEARS_NOT_PROSPECTIVE");
 assert.equal(report.country_years,321);
 assert.equal(report.positive_threshold_entries,8);
 assert.equal(x.n,321);
 assert.equal(x.entries,8);
 assert.deepEqual(x.target_years,[2024,2025]);
 assert.equal(x.model_brier,report.pooled_scores.p_model.brier);
 assert.equal(x.entry_prior_brier,report.pooled_scores.p_entry_prior_2y.brier);
 assert.equal(x.global_markov_brier,report.pooled_scores.p_global_markov.brier);
 assert.ok(x.model_brier<x.entry_prior_brier);
 assert.equal(report.folds[0].entry_training.historical_last_eligible_origin_year,2020);
 assert.equal(report.folds[1].entry_training.historical_last_eligible_origin_year,2021);
 assert.deepEqual(x.folds.map(v=>[v.year,v.n,v.entries]),[[2024,159,4],[2025,162,4]]);
 assert.equal(x.folds[0].top_5_hits,2);
 assert.equal(x.folds[1].top_5_hits,1);
 assert.ok(x.forecast_over_outcome_ratio>1.6);
 assert.ok(x.country_bootstrap_95_delta_brier_vs_entry_prior[0]<0);
 assert.ok(x.country_bootstrap_95_delta_brier_vs_entry_prior[1]>0);
 assert.equal(x.original_2027_probabilities_unchanged,true);
 assert.equal(x.resolved_2027_forecasts,0);
 assert.equal(x.prospectively_verified,false);
 assert.equal(report.real_2027_predictions_changed,0);
 assert.equal(report.real_2027_outcomes_resolved,0);
 assert.equal(verifyResearch(registry),true);
 const ui=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(ui,/function renderNewEntryComparator/);
 assert.match(ui,/renderNewEntryComparator\(\)\+renderOriginStateSkill\(\)/);
 assert.match(ui,/incluye cero/);
 assert.match(ui,/forecast-2027-entry-comparison\.json/);
});
test("reject retroactive changes to archived entry comparator or claimed future skill",()=>{
 let r=structuredClone(registry);
 r.new_entry_2027_comparison.prospectively_verified=true;
 assert.throws(()=>verifyResearch(r),/Cannot present post-hoc threshold entry/);
 r=structuredClone(registry);
 r.new_entry_2027_comparison.original_2027_probabilities_unchanged=false;
 assert.throws(()=>verifyResearch(r),/Cannot present post-hoc threshold entry/);
 r=structuredClone(registry);
 r.new_entry_2027_comparison.source_vintages["23.1"].sha256="0".repeat(64);
 assert.throws(()=>verifyResearch(r),/Entry comparator official source/);
 r=structuredClone(registry);
 r.new_entry_2027_comparison.entry_prior_brier=0;
 assert.throws(()=>verifyResearch(r),/Entry comparator Brier/);
 r=structuredClone(registry);
 r.new_entry_2027_comparison.folds[1].top_5_hits=5;
 assert.throws(()=>verifyResearch(r),/Entry comparator year-wise/);
 r=structuredClone(registry);
 r.new_entry_2027_comparison.country_bootstrap_95_delta_brier_vs_entry_prior=[-1,-0.1];
 assert.throws(()=>verifyResearch(r),/Entry comparator Brier/);
});

test("homogeneous onset2 23.1-to-25.1 shows poor ranking on two rare war onsets",()=>{
 const x=registry.onset2_homogeneous_vintage;
 const full=JSON.parse(readFileSync(new URL("../data/onset2-231-251-homogeneous.json",import.meta.url),"utf8"));
 assert.equal(x.id,"EMP-GEO-ONSET2-231-251-HOMOGENEOUS-20261110");
 assert.equal(x.model_kind,"COUNTRY_EMPIRICAL_BAYES_REGULARIZED_RATE_NOT_TWO_STEP_MARKOV");
 assert.equal(full.schema,"idealab.psico.onset2_homogeneous_231_to_251.v1");
 assert.equal(x.country_years,392);
 assert.equal(x.events,2);
 assert.equal(full.events,2);
 assert.deepEqual(x.assessed_years,[2023,2024]);
 assert.equal(x.vintage_label_flips,2);
 assert.equal(x.vintage_common_country_years,12161);
 assert.equal(x.legacy19_excluded,true);
 assert.equal(full.legacy_19_1_included,false);
 assert.ok(x.model_brier>x.global_brier);
 assert.ok(x.model_brier>x.recent_brier);
 assert.ok(x.model_brier>x.no_onset_brier);
 assert.ok(x.brier_skill_global<0);
 assert.equal(x.years.every(y=>y.events===1&&y.n===196&&y.top_20_hits===0),true);
 assert.equal(x.prospective_2027_results_resolved,0);
 assert.equal(x.predictive_skill_demonstrated,false);
 assert.equal(x.prospective_2027_forecasts_unchanged,true);
 assert.equal(registry.forecast_issued,1);
 assert.equal(registry.prospective_results_verified,0);
 assert.equal(verifyResearch(registry),true);
 const ui=readFileSync(new URL("../src/site.mjs",import.meta.url),"utf8");
 assert.match(ui,/function renderOnset2Homogeneous/);
 assert.match(ui,/no el modelo Markov de dos pasos/);
 assert.match(ui,/Ninguno de los dos inicios aparece/);
});
test("negative onset2 model outcome cannot be reframed as validated skill",()=>{
 let d=structuredClone(registry);
 d.onset2_homogeneous_vintage.predictive_skill_demonstrated=true;
 assert.throws(()=>verifyResearch(d),/Unverified homogeneous onset2/);
 d=structuredClone(registry);
 d.onset2_homogeneous_vintage.legacy19_excluded=false;
 assert.throws(()=>verifyResearch(d),/Unverified homogeneous onset2/);
 d=structuredClone(registry);
 d.onset2_homogeneous_vintage.sources["23.1"].sha256="0".repeat(64);
 assert.throws(()=>verifyResearch(d),/Homogeneous onset2 source files/);
 d=structuredClone(registry);
 d.onset2_homogeneous_vintage.model_brier=0.00001;
 assert.throws(()=>verifyResearch(d),/Homogeneous onset2 negative result/);
 d=structuredClone(registry);
 d.onset2_homogeneous_vintage.years[0].top_20_hits=1;
 assert.throws(()=>verifyResearch(d),/Onset2 year-specific ranking/);
 d=structuredClone(registry);
 d.onset2_homogeneous_vintage.bootstrap_country95_model_minus_global=[-.03,-.01];
 assert.throws(()=>verifyResearch(d),/Onset2 uncertainty interval/);
});
