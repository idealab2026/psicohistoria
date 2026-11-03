/** Read-only public catalogue presentation. No writes or mutable status. */
const safe=v=>String(v??"").replace(/[&<>"']/g,c=>({
 "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
const heading=(name,n)=>'<div class="portfolio-group-heading"><h3>'+safe(name)+
 '</h3><span>'+n+' fichas</span></div>';
const detail=(label,text)=>text?'<div class="portfolio-detail-item"><dt>'+safe(label)+
 '</dt><dd>'+safe(text)+'</dd></div>':"";
function card(project,relations){
 const d=project.documentation||{};
 const links=relations.filter(x=>x.sourceProjectId===project.id);
 const destinations=new Map(project._labels);
 return '<article class="portfolio-card" id="portfolio-'+safe(project.id)+'">'+
  '<div class="portfolio-card-head"><span class="portfolio-kind">'+safe(project.alias)+
  '</span><span class="portfolio-state">Estado en archivo: '+safe(project.status)+'</span></div>'+
  '<h4>'+safe(project.name)+'</h4>'+
  '<p>'+safe(project.summary)+'</p>'+
  '<div class="portfolio-quick"><span>'+safe(project.type)+'</span>'+
  '<span>Actualizado en origen: '+safe(project.updatedAt)+'</span></div>'+
  '<details><summary>Ficha científica y relaciones</summary>'+
  '<dl class="portfolio-detail">'+
  detail("Visión",d.vision)+detail("Objetivo",d.objective)+
  detail("Alcance",d.scope)+detail("Estado documentado entonces",d.currentState)+
  detail("Hitos previstos entonces",d.milestones)+
  detail("Reglas científicas",d.rules)+
  (!d.vision?detail("Documentación","No acreditada en este archivo histórico."): '')+
  '</dl>'+
  '<div class="portfolio-relations"><strong>Relaciones del proyecto</strong>'+
  (links.length?'<ul>'+links.map(r=>'<li><span>'+safe(r.type.replaceAll("_"," ").toLowerCase())+
   '</span> · '+safe(destinations.get(r.target)||r.target)+
   '<small>'+safe(r.description)+'</small></li>').join("")+'</ul>':
   '<p>No se registran relaciones salientes en esta copia.</p>')+
  '</div>'+
  '<p class="portfolio-disclaimer">La ficha refleja su estado histórico; no verifica avances posteriores, emisiones ni capacidad predictiva.</p>'+
  '</details></article>';
}
export function renderHistoricalProjectPortfolio(catalog){
 if(!catalog)return '<div class="panel"><h3>Catálogo no disponible</h3>'+
  '<p>La fuente institucional no está cargada o no supera su validación. No se reconstruyen proyectos con datos de demostración.</p></div>';
 const ids=new Map([...catalog.projects,...catalog.externalReferences].map(p=>[p.id,p.name]));
 const enrich=p=>({...p,_labels:ids});
 const core=["prj-psico-cliodinamica","prj-psico-forecast","prj-psico-agentes","prj-psico-metalab"];
 const apps=["prj-psico-agenda","prj-psico-transmision","prj-psico-radar"];
 const groups=[
  {name:"Programa y arquitectura",ids:["prj-psicohistoria","prj-idea-lab-sistemas-publico"]},
  {name:"Cuatro vertientes científicas",ids:core},
  {name:"Tres aplicaciones",ids:apps}
 ];
 return '<header class="section-head"><div class="eyebrow">CREAR · CARTERA DE IDEAS</div>'+
  '<h2>Catálogo de investigación recuperado</h2>'+
  '<p>Nueve expedientes y catorce relaciones conservados de una fotografía histórica. Los estados no son una lectura operativa de hoy.</p></header>'+
  '<div class="portfolio-numbers"><div><strong>4</strong><span>Vertientes</span></div>'+
  '<div><strong>3</strong><span>Aplicaciones</span></div>'+
  '<div><strong>14</strong><span>Relaciones</span></div>'+
  '<div><strong>8</strong><span>Fichas documentadas</span></div></div>'+
  '<p class="portfolio-disclaimer">'+safe(catalog.notice)+
  ' No se transfieren código privado, rutas internas ni registros personales.</p>'+
  groups.map(g=>'<section class="portfolio-group">'+heading(g.name,g.ids.length)+
   '<div class="portfolio-grid">'+g.ids.map(id=>card(enrich(catalog.projects.find(p=>p.id===id)),catalog.relations)).join("")+
   '</div></section>').join("")+
  '<p class="portfolio-disclaimer">Una relación con otra línea de IDEA LAB describe una posibilidad metodológica, no una transferencia de posiciones o señales de inversión.</p>';
}
