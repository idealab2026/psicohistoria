// IDEA LAB · institutional, offline-only research tool.
// An as-of audit is meaningful only when release dates and hashes are independently verified.
// These functions NEVER certify a historical issue or an actual prospective prediction.
const day = value => {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value) ||
      !Number.isFinite(Date.parse(value)) ||
      new Date(value).toISOString().slice(0, 10) !== value)
    throw Error("Invalid ISO date");
  return value;
};
const binary = v => v === 0 || v === 1;
const safeProbability = p => Math.min(1 - 1e-12, Math.max(1e-12, p));
const mean = values => values.reduce((a, b) => a + b, 0) / values.length;

function validateRows(rows) {
  if (!Array.isArray(rows) || !rows.length || rows.length > 50000)
    throw Error("Invalid country-year sample");
  const used = new Set();
  for (const row of rows) {
    if (!row || !/^[A-Z][A-Z0-9_-]{1,15}$/.test(row.country || "") ||
        !Number.isSafeInteger(row.year) || row.year < 1900 || row.year > 2100 ||
        !binary(row.outcome) || !binary(row.prior_conflict_active) ||
        !/^[a-f0-9]{64}$/.test(row.source_sha256 || ""))
      throw Error("Invalid source-backed country-year row");
    const key = row.country + ":" + row.year;
    if (used.has(key)) throw Error("Duplicate country-year record");
    used.add(key);
    day(row.source_release_at);
    day(row.prior_state_available_at);
    day(row.label_available_at);
    if (row.label_available_at <= String(row.year).padStart(4, "0") + "-01-01")
      throw Error("Outcome is dated before the observation period");
  }
}

function score(rows, field) {
  return {
    brier: mean(rows.map(r => (r[field] - r.outcome) ** 2)),
    logloss: mean(rows.map(r => {
      const p = safeProbability(r[field]);
      return -(r.outcome * Math.log(p) + (1 - r.outcome) * Math.log1p(-p));
    }))
  };
}

export function evaluateRollingOrigin(rows, options) {
  validateRows(rows);
  if (!options || !Number.isSafeInteger(options.first_test_year) ||
      !Number.isSafeInteger(options.last_test_year) ||
      options.first_test_year > options.last_test_year ||
      options.last_test_year - options.first_test_year > 30)
    throw Error("Invalid fixed test window");
  const lag = options.label_lag_years ?? 2;
  const strength = options.country_prior_strength ?? 20;
  const minTrain = options.min_training_observations ?? 20;
  const alertBudget = options.alerts_per_year ?? 5;
  if (!Number.isSafeInteger(lag) || lag < 1 || lag > 10 ||
      !Number.isFinite(strength) || strength <= 0 || strength > 10000 ||
      !Number.isSafeInteger(minTrain) || minTrain < 2 ||
      !Number.isSafeInteger(alertBudget) || alertBudget < 1 || alertBudget > 1000)
    throw Error("Invalid pre-registered protocol parameters");
  const evaluatedAt = day(options.evaluated_at);
  const all = [];
  const byYear = [];
  for (let year = options.first_test_year; year <= options.last_test_year; year++) {
    const target = rows.filter(r => r.year === year);
    if (!target.length) throw Error("Missing complete target year: " + year);
    const issuedAt = year + "-01-01";
    if (issuedAt >= evaluatedAt) throw Error("Target year is not historical");
    for (const r of target) {
      if (r.source_release_at >= issuedAt ||
          r.prior_state_available_at >= issuedAt)
        throw Error("Future target-year feature or source release (look-ahead)");
      if (r.label_available_at > evaluatedAt)
        throw Error("Target outcome not yet observable at evaluation");
    }
    const train = rows.filter(r => r.year <= year - lag &&
      r.source_release_at < issuedAt &&
      r.prior_state_available_at < issuedAt &&
      r.label_available_at < issuedAt);
    if (train.length < minTrain || new Set(train.map(r => r.year)).size < 3)
      throw Error("Insufficient admissible as-of training data");
    const global = (1 + train.reduce((sum, r) => sum + r.outcome, 0)) / (train.length + 2);
    const perState = new Map();
    const perCountryState = new Map();
    for (const r of train) {
      const s = r.prior_conflict_active;
      const g = perState.get(s) || {n:0, positives:0};
      g.n++; g.positives += r.outcome; perState.set(s, g);
      const key = r.country + ":" + s;
      const c = perCountryState.get(key) || {n:0, positives:0};
      c.n++; c.positives += r.outcome; perCountryState.set(key, c);
    }
    const predictions = target.map(r => {
      const group = perState.get(r.prior_conflict_active) || {n:0, positives:0};
      const conditional = (group.positives + 1) / (group.n + 2);
      const country = perCountryState.get(r.country + ":" + r.prior_conflict_active) || {n:0, positives:0};
      const model = (country.positives + strength * conditional) / (country.n + strength);
      return {
        year, country:r.country, outcome:r.outcome,
        model, global, conditional,
        issued_at:issuedAt, observed_at:r.label_available_at,
        source_sha256:r.source_sha256
      };
    });
    const ordered = [...predictions].sort((a,b) => b.model - a.model || a.country.localeCompare(b.country));
    const alerted = ordered.slice(0, alertBudget);
    const result = {
      year, n:target.length, positives:target.reduce((n,r)=>n+r.outcome,0),
      eligible_training_n:train.length,
      eligible_training_last_year:Math.max(...train.map(r=>r.year)),
      scores: {
        model:score(predictions,"model"),
        global:score(predictions,"global"),
        conditional:score(predictions,"conditional")
      },
      alert_budget:Math.min(alertBudget,target.length),
      true_alerts:alerted.filter(r=>r.outcome===1).length,
      false_alerts:alerted.filter(r=>r.outcome===0).length
    };
    byYear.push(result);
    all.push(...predictions);
  }
  if (!all.length) throw Error("No evaluable outcomes");
  const scores = {model:score(all,"model"), global:score(all,"global"), conditional:score(all,"conditional")};
  const bins = Array.from({length:5},(_,i) => {
    const matched=all.filter(r=>Math.min(4, Math.floor(r.model*5))===i);
    return {
      range:[i/5,(i+1)/5], n:matched.length,
      average_prediction:matched.length?mean(matched.map(r=>r.model)):null,
      empirical_rate:matched.length?mean(matched.map(r=>r.outcome)):null
    };
  });
  const positives=all.reduce((sum,r)=>sum+r.outcome,0);
  return {
    protocol:"RETROSPECTIVE_ROLLING_ORIGIN_ASOF_SELF_REPORTED",
    point_in_time_verified:false,
    issued_prospective_forecasts:0,
    verified_predictive_skill:false,
    outcome_count:all.length, positives, years:byYear, scores,
    brier_skill_vs_global:scores.global.brier>0?1-scores.model.brier/scores.global.brier:null,
    brier_skill_vs_conditional:scores.conditional.brier>0?1-scores.model.brier/scores.conditional.brier:null,
    logloss_change_vs_global:scores.model.logloss-scores.global.logloss,
    reliability_bins:bins, predictions:all,
    note:"Retrospective simulation only. Input release dates and SHA-256 are self-reported, not independently certified. No actual prospective issuance or operational utility has been demonstrated."
  };
}
