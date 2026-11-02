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
