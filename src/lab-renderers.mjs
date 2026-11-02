// Public visualizations of research concepts using only synthetic, in-memory inputs.
import {renderVerifiedGeometry} from "./markov-svg.mjs";
import {mountScientificNetwork} from "./neural.mjs";

const escape=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const TRACK=["V1","V2","V3","V4"];
export const TRANSITIONS=Object.freeze([
 Object.freeze([0.91,0.09,0,0]),
 Object.freeze([0,0,0.27,0.73]),
 Object.freeze([0.86,0.14,0,0]),
 Object.freeze([0,0,0.19,0.81])
]);
const STATE_LABELS=["00 · Bajo → bajo","01 · Entrada","10 · Salida","11 · Persistencia"];

export function scientificNeuralPanel(programs,selectedId) {
 if(!Array.isArray(programs)||programs.length!==4)throw new Error("FOUR_TRACKS_REQUIRED");
 return '<section class="panel science-neural-panel" aria-label="Mapa neuronal animado de investigación">'+
 '<div class="viz-heading"><div><div class="eyebrow">LABORATORIO / CUATRO VERTIENTES</div><h3>Red neuronal de investigación</h3></div>'+
 '<span class="viz-label">GEOMETRÍA CONCEPTUAL · NO DATOS CLÍNICOS NI RED ENTRENADA</span></div>'+
 '<div class="neural-stage" data-science-neural>'+
 '<canvas class="neural-canvas" aria-hidden="true"></canvas><div class="neural-grid" aria-hidden="true"></div>'+
 '<span class="neural-crosshair" aria-hidden="true">+</span>'+
 programs.map((p,i)=>'<button class="neural-orb" type="button" data-action="program" data-value="'+escape(p.id)+
 '" data-track="'+TRACK[i]+'" aria-pressed="'+String(selectedId===p.id)+'">'+
 '<span class="orb-sphere" aria-hidden="true"><span>'+TRACK[i]+'</span></span>'+
 '<strong>'+escape(p.name)+'</strong></button>').join("")+
 '<div class="neural-signature"><span>IDEA LAB</span><small>INVESTIGACIÓN · SISTEMAS COMPLEJOS</small></div>'+
 '<button type="button" data-motion-toggle class="motion-toggle" aria-pressed="false">Pausar movimiento</button></div>'+
 '<p class="viz-foot">Visualización conceptual de cuatro líneas de investigación. No representa una red neuronal entrenada ni resultados predictivos.</p></section>';
}

export function enableScientificNeural(root,programs,selectedId){
 const stage=root?.querySelector("[data-science-neural]");
 if(!stage)return ()=>{};
 const selected=Math.max(0,programs.findIndex(p=>p.id===selectedId));
 return mountScientificNetwork(stage,{activeTrack:TRACK[selected]});
}


// Six mutually consistent questions from ONE synthetic four-state probability vector.
export const PUBLIC_TREE_QUESTIONS=Object.freeze([
 {id:"atleast25",name:"25 o más muertes en el año",states:[1,3]},
 {id:"below25",name:"Menos de 25 muertes en el año",states:[0,2]},
 {id:"entry",name:"Entrar en el episodio agregado",states:[1]},
 {id:"exit",name:"Salir del episodio agregado",states:[2]},
 {id:"persistence",name:"Persistir por encima del umbral",states:[3]},
 {id:"stable_low",name:"Permanecer bajo el umbral",states:[0]}
].map(q=>Object.freeze({...q,states:Object.freeze(q.states)})));
const STATE_MEANINGS=[
 "Dos años por debajo del umbral",
 "Cruza de bajo a 25 o más",
 "Desciende de 25 o más a bajo",
 "Dos años con 25 o más"
];
export function syntheticTreeQuestion(model,horizon,question="atleast25"){
 const q=PUBLIC_TREE_QUESTIONS.find(x=>x.id===question);
 if(!q||!Number.isInteger(horizon)||horizon<1||horizon>model?.maxHorizon)
  throw new Error("INVALID_ILLUSTRATIVE_QUESTION");
 const masses=model.snapshots[horizon-1]?.distribution;
 if(!Array.isArray(masses)||masses.length!==4||
    masses.some(x=>typeof x!=="number"||!Number.isFinite(x)||x<0||x>1)||
    Math.abs(masses.reduce((a,b)=>a+b,0)-1)>1e-9)
  throw new Error("INVALID_SYNTHETIC_DISTRIBUTION");
 const yes=q.states.reduce((total,i)=>total+masses[i],0);
 return {id:q.id,name:q.name,year:model.snapshots[horizon-1].endYear,
  yes,no:1-yes,matched:[...q.states]};
}
const answerPct=n=>new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(n);

export const PUBLIC_CALENDAR_ORIGINS=Object.freeze([2016,2020]);
export function syntheticFourStateModel(periods=6,origin=2020){
 if(!PUBLIC_CALENDAR_ORIGINS.includes(origin))throw new Error("INVALID_ILLUSTRATIVE_ORIGIN");
 const maxHorizon=2026-origin;
 if(!Number.isInteger(periods)||periods<1||periods>maxHorizon)throw new Error("INVALID_HORIZON");
 // These are merely calendar labels for a synthetic illustration. The
 // transitions, country and outputs do NOT reproduce the private catalog.
 let distribution=[1,0,0,0];
 const cutoff=origin-2;
 const levels=[{year:cutoff,distribution:[...distribution],flows:[]}];
 for(let step=1;step<=periods+1;step++){
  const flows=[],next=[0,0,0,0];
  for(let from=0;from<4;from++)for(let to=0;to<4;to++){
   const conditional=TRANSITIONS[from][to],mass=distribution[from]*conditional;
   if(mass>0)flows.push({from,to,conditional,mass});
   next[to]+=mass;
  }
  distribution=next;
  levels.push({year:cutoff+step,distribution:[...distribution],flows});
 }
 return {origin,cutoff,maxHorizon:periods,country:{name:"Ejemplo sintético"},initial:0,
  levels,states:STATE_LABELS,observedStates:[],snapshots:Array.from({length:periods},(_,i)=>({
   endYear:origin+i,distribution:levels[i+2].distribution,
   paths:[],interval95:null
  }))};
}

export function scientificMarkovPanel({horizon=6,selection=null,origin=2020,question="atleast25"}={}){
 if(!PUBLIC_CALENDAR_ORIGINS.includes(origin))throw new Error("INVALID_ILLUSTRATIVE_ORIGIN");
 const maxHorizon=2026-origin;
 if(!Number.isInteger(horizon)||horizon<1||horizon>maxHorizon)throw new Error("INVALID_SELECTION");
 const data=syntheticFourStateModel(maxHorizon,origin);
 const graph=renderVerifiedGeometry(data,horizon,selection,false,true);
 const answer=syntheticTreeQuestion(data,horizon,question);
 const questionOptions=PUBLIC_TREE_QUESTIONS.map(q=>
  '<option value="'+q.id+'"'+(q.id===question?' selected':'')+'>'+escape(q.name)+'</option>').join("");
 const questionPanel='<div class="science-prediction-question">'+
  '<label>¿Qué quieres calcular a partir del mismo árbol?'+
  '<select data-public-question aria-label="Pregunta hipotética a calcular">'+questionOptions+
  '<optgroup label="Sin modelo ni probabilidades"><option disabled>Guerra nueva</option>'+
  '<option disabled>Decisiones políticas</option><option disabled>Movimientos de mercados</option></optgroup>'+
  '</select></label>'+
  '<div class="science-question-result"><div><small>SÍ · '+answer.year+
  '</small><strong>'+answerPct(answer.yes)+'</strong></div>'+
  '<div><small>NO · '+answer.year+'</small><strong>'+answerPct(answer.no)+'</strong></div></div>'+
  '<p>Porcentajes exclusivamente sintéticos. Las seis preguntas utilizan la misma distribución de cuatro estados: cambiar la pregunta no entrena otro modelo.</p></div>';
 const statesGuide='<div class="science-tree-states" aria-label="Significado de los nodos 00 01 10 11">'+
  STATE_LABELS.map((title,i)=>'<div class="science-tree-state'+(answer.matched.includes(i)?' matches-question':'')+
  '"><strong>'+escape(title)+'</strong><small>'+escape(STATE_MEANINGS[i])+'</small>'+
  (answer.matched.includes(i)?'<em>Responde SÍ</em>':'')+'</div>').join("")+'</div>';

 const inspection=selection?.kind==="node"?
  "Nodo "+data.levels[selection.level]?.year+": "+(STATE_LABELS[selection.state]||"No válido")+" · "+
   new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:2}).format(data.levels[selection.level]?.distribution[selection.state]??0):
  selection?.kind==="edge"?"Transición seleccionada en "+data.levels[selection.level]?.year:
  "Selecciona un año, un nodo o una transición. Se conserva el árbol completo del mismo origen.";
 const originButtons=PUBLIC_CALENDAR_ORIGINS.map(y=>
  '<button type="button" class="ghost '+(y===origin?'active':'')+
  '" data-action="markov-origin" data-value="'+y+'" aria-pressed="'+String(y===origin)+
  '">Origen '+y+' · ejemplo</button>').join("");
 const strip=data.levels.map((level,i)=>{
  const active=i===horizon+1;
  const state=i===0?"último dato (simulado)":i===1?"puente (simulado)":active?"inspeccionado":"proyección (simulada)";
  const opening=i<2?'<span class="future-year-static" aria-label="'+level.year+' · '+state+'">':
    '<button type="button" class="future-year-select'+(active?' active':'')+
    '" data-action="markov-year" data-value="'+(i-1)+'" aria-pressed="'+String(active)+'" aria-label="Inspeccionar '+level.year+'">';
  return opening+'<strong>'+level.year+'</strong><small>'+state+'</small>'+(i<2?'</span>':'</button>');
 }).join("");
 return '<section class="panel science-markov-panel" aria-label="Árbol temporal ilustrativo de cuatro estados">'+
 '<div class="viz-heading"><div><div class="eyebrow">ESTRUCTURA TEMPORAL · CALENDARIO ILUSTRATIVO</div>'+
 '<h3>Árbol de predicciones · '+origin+'–2025</h3></div><span class="viz-label">MALLA SINTÉTICA · NINGÚN PAÍS REAL</span></div>'+
 '<div class="markov-origin-controls" role="group" aria-label="Año inicial del árbol ilustrativo">'+originButtons+'</div>'+
 '<p class="markov-timeline-explainer">Años visibles en el árbol: <b>'+data.cutoff+'</b> (último dato ficticio) · <b>'+(origin-1)+
 '</b> (puente sin observación) · <b>'+origin+'–2025</b> (años de proyección). '+
 'Ninguna probabilidad procede de las cohortes históricas privadas.</p>'+
 questionPanel+
 '<nav class="future-year-strip" aria-label="Todos los años naturales del árbol">'+strip+'</nav>'+
 '<div class="future-graph-scroll" data-science-markov tabindex="0" role="region" aria-label="Árbol de años '+data.cutoff+' a 2025; desliza horizontalmente para verlos todos">'+graph+'</div>'+
 statesGuide+
 '<div class="future-selection-note" role="status">'+escape(inspection)+'</div>'+
 '<div class="science-state-legend">'+STATE_LABELS.map((n,i)=>'<span data-state="'+i+'">'+escape(n)+'</span>').join("")+'</div>'+
 '<p class="viz-foot">Calendario real de años, probabilidades y resultados totalmente ficticios. No hay evaluación ni emisión científica; los árboles históricos autentificados requieren el entorno privado.</p></section>';
}
