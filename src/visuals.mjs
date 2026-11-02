// Independent institutional visualizations: structure only, no historical records.
// These diagrams never infer causation, posterior evidence or numeric forecasts.
const clean=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const percent=n=>Number.isFinite(n)?new Intl.NumberFormat("es-ES",{style:"percent",maximumFractionDigits:1}).format(n):"—";
const positions=[[18,16],[50,7],[82,16],[87,56],[66,85],[34,85],[12,56]];
const hue=["ice","gold","mint","violet"];
const codes=["00","01","10","11"];
const names=["Bajo → bajo","Entrada","Salida","Persistencia"];
const transitions=Object.freeze({"00":["00","01"],"01":["10","11"],"10":["00","01"],"11":["10","11"]});

export function researchOrbs(programs, selectedId) {
 if(!Array.isArray(programs)||programs.length!==4||programs.some(p=>!p||!p.id||!p.name))return "";
 return '<section class="research-orbs panel" aria-label="Constelación de las cuatro vertientes del laboratorio">'+
  '<div class="viz-heading"><div><div class="eyebrow">ARQUITECTURA DE INVESTIGACIÓN</div><h3>Cuatro vertientes conectadas</h3></div>'+
  '<span class="viz-label">GEOMETRÍA CONCEPTUAL · SIN VALORES CIENTÍFICOS</span></div>'+
  '<div class="orb-field"><svg class="orb-connections" viewBox="0 0 1000 420" preserveAspectRatio="none" aria-hidden="true">'+
  '<g fill="none" stroke="#527c98" stroke-width="1.4" stroke-dasharray="5 9" opacity=".55"><path d="M500 210 L205 112 M500 210 L795 112 M500 210 L205 320 M500 210 L795 320"/></g>'+
  '<circle cx="500" cy="210" r="86" fill="none" stroke="#527d99" stroke-dasharray="2 10" opacity=".65"/>'+
  '<circle cx="500" cy="210" r="120" fill="none" stroke="#284a62" opacity=".5"/></svg>'+
  '<div class="orb-core" aria-hidden="true"><span>IDEA LAB</span><small>SISTEMAS COMPLEJOS</small></div>'+
  programs.map((p,i)=>'<button type="button" class="orb-node orb-'+i+' '+(p.id===selectedId?"active":"")+
  '" data-action="program" data-value="'+clean(p.id)+'" aria-pressed="'+String(p.id===selectedId)+'">'+
  '<span class="orb-sphere orb-'+hue[i]+'" aria-hidden="true"><i></i><i></i><i></i></span>'+
  '<strong>'+clean(p.name)+'</strong><small>'+clean(p.state||"En investigación")+'</small></button>').join("")+'</div>'+
  '<p class="viz-foot">Pulsa un orbe para inspeccionar su metodología. Las conexiones representan un programa de trabajo, no dependencias causales.</p></section>';
}

export function scenarioBranches(branches,selectedId) {
 if(!Array.isArray(branches)||branches.length<2||branches.length>5||
 branches.some(b=>!b||typeof b.id!=="string"||typeof b.name!=="string"||!Number.isFinite(b.weight)||b.weight<0||b.weight>1))return "";
 if(Math.abs(branches.reduce((s,b)=>s+b.weight,0)-1)>1e-7)return "";
 return '<section class="panel scenario-network" aria-label="Árbol de escenarios hipotéticos">'+
 '<div class="viz-heading"><div><div class="eyebrow">ÁRBOL DE POSIBILIDADES</div><h3>Origen único · '+branches.length+' alternativas</h3></div>'+
 '<span class="viz-label">PESOS INTRODUCIDOS · DEMOSTRACIÓN</span></div>'+
 '<div class="scenario-layout"><div class="scenario-root"><span class="scenario-pulse" aria-hidden="true"></span><b>SUPUESTOS</b><small>T0 · origen ficticio</small></div>'+
 '<div class="scenario-forks">'+branches.map((b,i)=>'<button type="button" class="scenario-leaf '+(selectedId===b.id?'active':'')+
 '" data-action="scenario" data-value="'+clean(b.id)+'" aria-pressed="'+String(selectedId===b.id)+'">'+
 '<small>T1 · RAMA '+(i+1)+'</small><strong>'+clean(b.name)+'</strong><span>'+percent(b.weight)+'</span>'+
 '<i class="scenario-fill" style="--prob:'+Math.round(b.weight*100)+'%" aria-hidden="true"></i></button>').join("")+'</div></div>'+
 '<p class="viz-foot">Un árbol visual no demuestra capacidad predictiva. Los porcentajes no proceden de datos históricos ni tienen intervalo de confianza.</p></section>';
}

export function stateTransitionDiagram(selected="00") {
 if(!codes.includes(selected))selected="00";
 const valid=transitions[selected];
 const nodes=codes.map((code,i)=>'<button type="button" class="state-node state-node-'+code+' '+(selected===code?'active':'')+
 '" data-action="state-flow" data-value="'+code+'" aria-pressed="'+String(code===selected)+'">'+
 '<small>'+code+'</small><b>'+names[i]+'</b></button>').join("");
 return '<section class="panel transition-visual" aria-label="Diagrama conceptual de transiciones entre cuatro estados">'+
 '<div class="viz-heading"><div><div class="eyebrow">ESTADOS Y TRANSICIONES</div><h3>Cuatro estados observables</h3></div>'+
 '<span class="viz-label">SIN PARÁMETROS REALES</span></div>'+
 '<div class="state-grid">'+nodes+'</div>'+
 '<div class="state-edges"><div class="state-current"><small>ESTADO SELECCIONADO · T</small><strong>'+selected+' · '+clean(names[codes.indexOf(selected)])+'</strong></div>'+
 '<div class="state-arrow" aria-hidden="true">⟶</div><div class="state-next"><small>TRANSICIONES PERMITIDAS · T+1</small>'+
 valid.map(v=>'<span class="state-destination">'+v+' · '+clean(names[codes.indexOf(v)])+'</span>').join("")+'</div></div>'+
 '<p class="viz-foot">00 = ambos años bajo el umbral; 01 = entrada; 10 = salida; 11 = persistencia. El estado del año siguiente conserva el segundo componente como primero. Este diagrama no usa predicciones históricas.</p></section>';
}

export function domainGraph(programs, selectedDomain="todos") {
 if(!Array.isArray(programs)||programs.length!==7||programs.some(p=>!p||!p.title||!p.domain))return "";
 return '<section class="panel domain-graph" aria-label="Mapa visual de siete líneas de investigación">'+
 '<div class="viz-heading"><div><div class="eyebrow">CARTOGRAFÍA CIENTÍFICA</div><h3>Siete líneas, un protocolo común</h3></div><span class="viz-label">FUENTES IDENTIFICADAS · SIN RESULTADOS PROSPECTIVOS</span></div>'+
 '<div class="domain-stage"><svg viewBox="0 0 1000 440" preserveAspectRatio="none" aria-hidden="true" class="domain-lines">'+
 '<g fill="none" stroke="#47758c" stroke-width="1.4" opacity=".65">'+positions.map(([x,y])=>
 '<path d="M500 218 Q'+(x*10)+' '+(y*4.4+150)+' '+(x*10)+' '+(y*4.4)+'" stroke-dasharray="4 8"/>').join("")+
 '</g><circle cx="500" cy="218" r="99" stroke="#31576a" fill="none" stroke-dasharray="1 10"/></svg>'+
 '<div class="domain-core"><strong>IDEA LAB</strong><small>PROGRAMA CIENTÍFICO</small></div>'+
 programs.map((p,i)=>'<button class="domain-node '+(p.domain===selectedDomain?'active':'')+
 '" type="button" style="--dx:'+positions[i][0]+'%;--dy:'+positions[i][1]+'%" data-action="registry-filter" data-value="'+clean(p.domain)+
 '" title="'+clean(p.question||p.title)+'"><small>'+clean(p.id||"")+'</small><strong>'+clean(p.title)+
 '</strong><span>'+clean(p.stage||"Protocolo")+'</span></button>').join("")+'</div>'+
 '<p class="viz-foot">Selecciona una línea para filtrar la tabla de fuentes. Las aristas significan normas metodológicas compartidas, no relaciones causales entre fenómenos.</p></section>';
}
