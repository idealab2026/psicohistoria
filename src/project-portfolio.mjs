/** Institutional, privacy-independent methodological presentation; no mutable status. */
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({
 "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
}[c]));
const header=(name,count)=>'<div class="portfolio-group-heading"><h3>'+esc(name)+
 '</h3><span>'+count+' fichas</span></div>';
const detail=(label,value)=>value?'<div class="portfolio-detail-item"><dt>'+esc(label)+
 '</dt><dd>'+esc(value)+'</dd></div>':"";
function card(project,relations,names){
 const d=project.documentation||{};
 const outbound=relations.filter(r=>r.source===project.id);
 return '<article class="portfolio-card" id="portfolio-'+esc(project.id)+'">'+
  '<div class="portfolio-card-head"><span class="portfolio-kind">'+esc(project.category)+
  '</span><span class="portfolio-state">No certifica operación actual</span></div>'+
  '<h4>'+esc(project.name)+'</h4>'+
  '<p>'+esc(project.summary)+'</p>'+
  '<div class="portfolio-quick"><span>'+esc(project.area)+'</span>'+
  '<span>'+esc(project.subtitle)+'</span></div>'+
  '<details><summary>Metodología y conexiones</summary>'+
  '<dl class="portfolio-detail">'+detail("Enfoque",d.vision)+
  detail("Objeto de estudio",d.scope)+detail("Método",d.method)+
  detail("Validación pendiente",d.validation)+detail("Limitaciones",d.limitations)+
  '</dl>'+
  '<div class="portfolio-relations"><strong>Relaciones del programa</strong>'+
  (outbound.length?'<ul>'+outbound.map(r=>
    '<li><span>'+esc(r.type.replaceAll("_"," ").toLowerCase())+'</span> · '+
    esc(names.get(r.target)||"Referencia metodológica")+
    '<small>'+esc(r.description)+'</small></li>').join("")+'</ul>':
    '<p>No constan relaciones salientes en esta proyección.</p>')+
  '</div>'+
  '<p class="portfolio-disclaimer">'+esc(project.stageNote)+'</p>'+
  '</details></article>';
}
export function renderHistoricalProjectPortfolio(catalog){
 if(!catalog||catalog.status!=="PUBLIC_INSTITUTIONAL_PROJECTION")
  return '<div class="panel"><h3>Catálogo no disponible</h3>'+
   '<p>El archivo institucional no está disponible o no supera la validación. No se generan proyectos de respaldo.</p></div>';
 const names=new Map([...catalog.projects,...catalog.externalReferences].map(p=>[p.id,p.name]));
 const groups=[
  ["Programa científico",catalog.projects.filter(p=>p.category==="Programa")],
  ["Cuatro vertientes",catalog.projects.filter(p=>p.category==="Vertiente")],
  ["Tres aplicaciones",catalog.projects.filter(p=>p.category==="Aplicación")],
  ["Laboratorio público",catalog.projects.filter(p=>p.category==="Plataforma")]
 ];
 return '<header class="section-head"><div class="eyebrow">CREAR · CARTERA DE IDEAS</div>'+
  '<h2>Ideas y aplicaciones</h2>'+
  '<p>Programa metodológico institucional: cuatro vertientes y tres aplicaciones de investigación. Sin datos personales ni afirmaciones de rendimiento prospectivo.</p></header>'+
  '<div class="portfolio-numbers"><div><strong>4</strong><span>Vertientes</span></div>'+
  '<div><strong>3</strong><span>Aplicaciones</span></div>'+
  '<div><strong>9</strong><span>Proyectos</span></div>'+
  '<div><strong>14</strong><span>Relaciones</span></div></div>'+
  '<p class="portfolio-disclaimer">'+esc(catalog.notice)+
  ' La proyección pública utiliza identificadores nuevos y explicaciones independientes.</p>'+
  groups.map(([name,projects])=>
   '<section class="portfolio-group">'+header(name,projects.length)+
   '<div class="portfolio-grid">'+projects.map(p=>card(p,catalog.relations,names)).join("")+
   '</div></section>').join("")+
  '<p class="portfolio-disclaimer">Las conexiones son conceptuales: no activan operaciones, reutilización de información personal ni una evaluación prospectiva.</p>';
}
