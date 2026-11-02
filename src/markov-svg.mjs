// Institutional adaptation of the existing scientific SVG topology; public inputs must be synthetic.
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = (value, digits = 3) => typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('es-ES', {maximumFractionDigits: digits}) : 'Sin datos';
const pct = value => fmt(value * 100, 2) + ' %';
const COLORS = ['#69c5f6', '#ff9b45', '#84d9bd', '#bdabff'];
const SHORT = ['Bajo → bajo', 'Entrada', 'Salida', 'Persistencia'];
const CODES = ['00','01','10','11'];
const REAL_EVENTS = [
  'Actividad estatal registrada por debajo del umbral de 25 muertes en ambos años; no implica paz ni ausencia de violencia.',
  'Entrada en episodio agregado: el año actual alcanza al menos 25 muertes estatales registradas tras un año bajo el umbral.',
  'Salida del episodio agregado: el año actual desciende por debajo del umbral tras un año que lo superó.',
  'Persistencia del episodio agregado: ambos años alcanzan al menos 25 muertes estatales registradas.'
];
const validObservedState = s => Number.isInteger(s) && s >= 0 && s <= 3;
const point = (level, state) => ({x: 76 + level * 126, y: level ? 90 + state * 83 : 215});
const curve = (from, to) => 'M' + from.x + ' ' + from.y + ' C' + (from.x + 60) + ' ' + from.y + ' ' + (to.x - 60) + ' ' + to.y + ' ' + to.x + ' ' + to.y;
function observedFact(result, level) {
  const state = result.observedStates?.[level];
  if (!validObservedState(state)) return null;
  const year = result.cutoff + level;
  const evidence = result.observedEvidence?.find(e => e?.year === year && Number.isInteger(e?.sbDeathsBest) && e.sbDeathsBest >= 0);
  const names = Array.isArray(evidence?.dyadNames) ? evidence.dyadNames.filter(n => typeof n === 'string' && n.length <= 320).slice(0,2) : [];
  return {year,state,title:SHORT[state],description:REAL_EVENTS[state],
    deaths:evidence?.sbDeathsBest,dyadCount:evidence?.sbDyadCount,names,
    source:evidence?.sourceUrl || 'https://ucdp.uu.se/downloads/'};
}
export function historicalEventCards(result,horizon) {
  if(!Array.isArray(result.observedStates))return '';
  const cards=[];
  for(let i=1;i<=horizon+1;i++) {
    const year=result.cutoff+i,fact=observedFact(result,i);
    if(!fact){cards.push('<article class="future-event-card"><small>'+year+' · NO EVALUABLE</small><strong>Sin observación válida para este año</strong></article>');continue;}
    const mortality=fact.deaths===undefined?
      (result.observedEvidenceStatus==='source_temporarily_unavailable'?'Detalle numérico de UCDP no disponible temporalmente':
      'Consultando datos oficiales UCDP…') :
      fmt(fact.deaths,0)+' muertes estatales · mejor estimación UCDP';
    const dyad=fact.deaths===undefined ?
      '<span class="future-dyad">Detalle de actores pendientes de verificar con UCDP</span>' :
      fact.names.length ? '<span class="future-dyad">Díadas registradas: '+fact.names.map(esc).join(' · ')+
      (fact.dyadCount>fact.names.length?' · y otras '+(fact.dyadCount-fact.names.length):'')+'</span>':
      '<span class="future-dyad">Ninguna díada estatal registrada en este país-año</span>';
    cards.push('<button type="button" class="future-event-card" data-fevent="'+i+'" aria-label="Inspeccionar acontecimiento UCDP '+
      fact.year+'"><small>'+fact.year+(i===1?' · PUENTE EX POST':' · AÑO OBJETIVO')+
      '</small><strong>'+CODES[fact.state]+' · '+esc(fact.title)+'</strong><span>'+
      esc(fact.description)+'</span><em>'+esc(mortality)+'</em>'+dyad+'</button>');
  }
  return '<div class="future-event-heading"><strong>Acontecimientos documentados en el recorrido real</strong><span>Datos conocidos después · Pulsa un año para inspeccionar</span></div>'+
    '<div class="future-event-cards">'+cards.join('')+'</div>'+
    '<p class="chart-note">Las díadas indican partes enfrentadas reportadas por UCDP; no son incidentes puntuales ni demuestran causalidad. El estado 00 no implica paz ni ausencia de otras violencias. Fuente: OrganizedViolenceCY 26.1, CC BY 4.0.</p>';
}
export function renderVerifiedGeometry(result, horizon, selection = null, observed = false, completeTree = false) {
  const shown = completeTree ? result.maxHorizon : horizon;
  const levels = result.levels.slice(0, shown + 2), width = 152 + (levels.length - 1) * 126;
  let svg = '<svg class="future-graph" viewBox="0 0 ' + width + ' 420" width="' + width + '" height="420" aria-label="Grafo temporal agregado de probabilidades. Las historias individuales se detallan debajo.">' +
    '<defs><radialGradient id="future-core"><stop stop-color="#fff3dd"/><stop offset=".16" stop-color="#ffbd7e"/><stop offset=".6" stop-color="#ff8a2855"/><stop offset="1" stop-color="#ff8a2800"/></radialGradient></defs>';
  if(completeTree)svg += '<path class="future-year-axis" d="M'+point(0,0).x+' 53 H'+point(levels.length-1,0).x+
    '" fill="none" stroke="#547287" stroke-width="1.5" aria-hidden="true"/>';
  levels.forEach((level, i) => {
    const inspected=completeTree && i === horizon + 1;
    if(inspected)svg+='<rect class="future-year-current" x="'+(point(i,0).x-45)+'" y="5" width="90" height="43" rx="8" aria-hidden="true"/>';
    const stage = i === 0 ? 'último dato' : i === 1 ? 'puente no observado' :
      completeTree ? (inspected?'proyección seleccionada':'proyección') : 'horizonte ' + (i - 1);
    svg += '<text class="future-year" x="' + point(i, 0).x + '" y="25" text-anchor="middle">' + level.year + '</text>' +
      '<text class="future-year-note" x="' + point(i, 0).x + '" y="43" text-anchor="middle">' + stage + '</text>';
    if (!i) return;
    level.flows.forEach((edge, index) => {
      if (edge.mass <= 0) return;
      const path = selection?.kind === 'path' ? result.snapshots[horizon-1].paths[selection.index] : null;
      const selected = (selection?.kind === 'edge' && selection.level === i && selection.index === index) || (path && path.states[i-1] === edge.from && path.states[i] === edge.to);
      const d = curve(point(i - 1, edge.from), point(i, edge.to));
      const from = point(i-1,edge.from), to = point(i,edge.to);
      svg += '<g class="future-edge" tabindex="0" role="button" data-fedge="' + i + ':' + index + '" aria-label="' + level.year + ', ' + esc(SHORT[edge.from]) + ' a ' + esc(SHORT[edge.to]) + '; condicional ' + pct(edge.conditional) + '; flujo ' + pct(edge.mass) + '"><title>Condicional ' + pct(edge.conditional) + ' · flujo agregado ' + pct(edge.mass) + '</title><path class="future-flow' + (selected ? ' selected' : '') + '" d="' + d + '" fill="none" stroke="' + COLORS[edge.to] + '" stroke-opacity="' + (selected ? '.95' : '.3') + '" stroke-width="' + (.5 + edge.mass * 14) + '"/><path d="'+d+'" fill="none" stroke="transparent" stroke-width="14"/><circle cx="'+((from.x+to.x)/2)+'" cy="'+((from.y+to.y)/2)+'" r="7" fill="transparent"/></g>';
      svg += '<path class="future-pulse" d="' + d + '" fill="none" stroke="' + COLORS[edge.to] + '" stroke-opacity=".8" stroke-width="1.6" stroke-dasharray="2 42" aria-hidden="true"/>';
    });
  });
  if (observed && result.observedStates?.length) {
    const states = result.observedStates.slice(0, levels.length);
    for (let i = 1; i < states.length; i++) if (validObservedState(states[i]) && validObservedState(states[i - 1])) {
      const d = curve(point(i - 1, states[i - 1]), point(i, states[i]));
      svg += '<path class="future-observed-halo" d="' + d + '" fill="none" stroke="#ffb35d" stroke-width="9" stroke-opacity=".23" aria-hidden="true"/>' +
        '<path class="future-observed" d="' + d + '" fill="none" stroke="#ffe4a8" stroke-width="3.7" stroke-dasharray="9 5"><title>Recorrido realmente observado después en la edición revisada UCDP</title></path>';
    }
  }
  levels.forEach((level, i) => level.distribution.forEach((mass, state) => {
    if (!i && state !== result.initial) return;
    const p = point(i, state), selected = selection?.kind === 'node' && selection.level === i && selection.state === state;
    svg += '<g class="future-node' + (selected ? ' selected' : '') + '" tabindex="0" role="button" data-fnode="' + i + ':' + state + '" aria-label="' + level.year + ', ' + esc(SHORT[state]) + ', probabilidad marginal ' + pct(mass) + '">';
    svg += '<rect x="' + (p.x-42) + '" y="' + (p.y-25) + '" width="84" height="80" fill="transparent"/>';
    if (!i) svg += '<circle class="future-core-glow" cx="' + p.x + '" cy="' + p.y + '" r="44" fill="url(#future-core)"/>';
    const realHere = observed && validObservedState(result.observedStates?.[i]) && result.observedStates[i] === state;
    if (realHere && i > 0) svg += '<circle class="future-real-ring" cx="' + p.x + '" cy="' + p.y +
      '" r="' + Math.max(15, Math.max(4, 20 * Math.sqrt(mass)) + 8) + '" fill="none" stroke="#ffdb9b" stroke-width="3" stroke-dasharray="4 3"><title>Estado observado después: ' +
      esc(SHORT[state]) + '</title></circle>';
    svg += '<circle cx="' + p.x + '" cy="' + p.y + '" r="' + (i ? Math.max(4, 20 * Math.sqrt(mass)) : 15) + '" fill="' + (i ? COLORS[state] : '#ffba78') + '" fill-opacity="' + (mass ? '.85' : '.12') + '" stroke="' + (selected ? '#fff' : COLORS[state]) + '" stroke-width="' + (selected ? 3 : 1) + '"/>' +
      '<text x="' + p.x + '" y="' + (p.y + 33) + '" text-anchor="middle" class="future-node-label">' + (i ? pct(mass) : 'ESTADO CONOCIDO') + '</text>' +
      (!i ? '<text x="' + p.x + '" y="' + (p.y + 50) + '" text-anchor="middle" class="future-year-note">' + esc(SHORT[state]) + '</text>' :
        realHere ? '<text x="' + p.x + '" y="' + (p.y - 33) + '" text-anchor="middle" class="future-real-label">' +
          (i === horizon + 1 ? 'REAL · FINAL' : 'REAL') + '</text>' : '') + '</g>';
    if (realHere && i > 0) {
      const fact = observedFact(result,i);
      svg += '<g class="future-event-marker" tabindex="0" role="button" data-fevent="'+i+
        '" aria-label="Evento real UCDP '+fact.year+': '+esc(fact.title)+'"><title>'+
        esc(fact.year+' · '+fact.description+(fact.deaths===undefined?'':'; '+fact.deaths+' muertes estatales estimadas'))+
        '</title><circle cx="'+(p.x+28)+'" cy="'+(p.y-20)+'" r="10" fill="#ffc182" stroke="#fff0d1" stroke-width="1"/>'+
        '<text x="'+(p.x+28)+'" y="'+(p.y-16)+'" text-anchor="middle" fill="#102439" font-size="12" font-weight="700">i</text></g>';
    }
  }));
  return svg + '</svg>';
}
