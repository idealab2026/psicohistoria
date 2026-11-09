import {makeDraft,validateNotebook,exportNotebook,describeScientificFile,searchScientificObject} from "./private-notebook.mjs";
import {createCountryComparison} from "./country-comparison-view.mjs";
const $=id=>document.getElementById(id);
const drafts=[],science=[];
const scientificDocuments=new Map();
const countryComparison=createCountryComparison();
let saved=true;
const status=(msg)=>$("work-status").textContent=msg;
const message=(t,text)=>{const x=document.createElement(t);x.textContent=text;return x;};
function render(){
 $("draft-count").textContent=String(drafts.length);
 $("loaded-count").textContent=String(science.length);
 const list=$("drafts-list");list.replaceChildren();
 if(!drafts.length){list.append(message("p","Todavía no hay borradores."));return;}
 for(const entry of [...drafts].reverse()){
   const box=document.createElement("article");box.className="item";
   const tag=message("span",entry.state);tag.className="badge-draft";
   box.append(tag,message("h3",entry.title),message("small",new Date(entry.created_at).toLocaleString("es-ES")),message("p",entry.question));
   const detail=document.createElement("details");
   detail.append(message("summary","Ver hipótesis, fuente y método"));
   const lines=[["Hipótesis",entry.hypothesis],["Método",entry.method],["Fuente",entry.source],["Ámbito",entry.target],["Notas",entry.notes]];
   for(const [name,val] of lines){if(val)detail.append(message("p",name+": "+val));}
   box.append(detail);list.append(box);
 }
}
const download=(name,text)=>{
 const blob=new Blob([text],{type:"application/json;charset=utf-8"});
 const url=URL.createObjectURL(blob),anchor=document.createElement("a");
 anchor.href=url;anchor.download=name;anchor.style.display="none";document.body.append(anchor);anchor.click();anchor.remove();
 setTimeout(()=>URL.revokeObjectURL(url),30000);
};
$("research-form").addEventListener("submit",e=>{
 e.preventDefault();
 try{
  const raw=Object.fromEntries(new FormData(e.currentTarget).entries());
  const item=makeDraft(raw,"WEB-"+crypto.randomUUID(),new Date().toISOString());
  drafts.push(item);saved=false;render();e.currentTarget.reset();
  status("Borrador "+item.id+" añadido solo en memoria. Exporta el expediente para conservarlo en la custodia institucional.");
 }catch(err){status("No se pudo añadir el borrador: "+String(err.message));}
});
$("export-notebook").addEventListener("click",()=>{
 try{
  if(!drafts.length){status("No hay ningún borrador que exportar.");return;}
  const text=exportNotebook(drafts,new Date().toISOString());
  download("idealab-psicohistoria-borradores-"+new Date().toISOString().slice(0,10)+".json",text);
  saved=true;status("Descarga preparada. Este fichero NO está sincronizado con Drive. Conserva la copia en la custodia institucional privada.");
 }catch(err){status("Exportación rechazada: "+String(err.message));}
});
$("notebook-file").addEventListener("change",async(e)=>{
 const file=e.target.files?.[0];if(!file)return;
 try{
  if(file.size>1024*1024)throw Error("CUADERNO_MAYOR_1_MB");
  const imported=validateNotebook(JSON.parse(await file.text()));
  const known=new Set(drafts.map(x=>x.id));
  let added=0;
  for(const row of imported){if(!known.has(row.id)){drafts.push(row);known.add(row.id);added++;}}
  render();saved=added===0&&saved;
  status("Se han leído "+imported.length+" borradores y añadido "+added+" nuevos. Expórtalos si realizas cambios.");
 }catch(err){status("No se admite el cuaderno: "+String(err.message));}
 finally{e.target.value="";}
});
$("science-files").addEventListener("change",async(e)=>{
 const files=Array.from(e.target.files||[]);
 if(files.length>8){status("Máximo ocho archivos JSON por lote.");return;}
 const summary=$("science-summary");
 for(const f of files){
  try{
   if(f.size>12*1024*1024)throw Error("LÍMITE_12_MB");
   if(!f.name.toLowerCase().endsWith(".json"))throw Error("SOLO_JSON");
   const bytes=await f.arrayBuffer();
   const decoded=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
   const info=describeScientificFile(decoded);
   const digest=await crypto.subtle.digest("SHA-256",bytes);
   const hash=Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,"0")).join("");
   const existing=science.find(x=>x.sha256===hash);
   if(!existing){
     science.push({name:f.name,sha256:hash,...info});
     scientificDocuments.set(hash,decoded);
     try{countryComparison.ingest(decoded);}
     catch(e){$("comparison-source-status").textContent="Catálogo Markov incompatible o no verificable: "+String(e.message)+". El archivo sigue disponible solo para inspección local.";}
   }
   status("Objetos interpretados localmente. Datos sin transmitir; comprueba los hashes con el archivo canónico.");
  }catch(err){status("Archivo rechazado ("+f.name+"): "+String(err.message));}
 }
 summary.replaceChildren();
 for(const info of science){
   const box=document.createElement("div");box.className="item";
   box.append(message("h3",info.name),message("small","SHA-256 "+info.sha256),message("p",info.kind+" · "+info.visibleArrayEntries+" elementos visibles en arrays · "+info.topLevelKeys.join(", ")));
   summary.append(box);
 }
 if(!science.length)summary.append(message("p","Ningún objeto válido cargado."));
 render();e.target.value="";
});
$("search-science").addEventListener("click",()=>{
 const root=$("search-science-results");root.replaceChildren();
 try{
  if(!science.length)throw Error("IMPORTA_PRIMERO_UN_JSON");
  const query=$("search-science-query").value;
  let total=0;
  for(const doc of science){
   if(total>=50)break;
   const {results,truncated}=searchScientificObject(scientificDocuments.get(doc.sha256),query,Math.min(40,50-total));
   for(const row of results){
     const item=document.createElement("div");item.className="item";
     item.append(message("small",doc.name),message("h3",row.path),message("p",row.preview));root.append(item);total++;
   }
   if(truncated)root.append(message("small","Resultados limitados para "+doc.name+"; afina la búsqueda."));
  }
  if(!total)root.append(message("p","No hay coincidencias en los objetos cargados."));
  status(total+" coincidencias consultadas solo en el navegador. No hay solicitudes a la red.");
 }catch(err){root.append(message("p","Búsqueda no disponible: "+String(err.message)));}
});
window.addEventListener("beforeunload",e=>{if(!saved&&drafts.length){e.preventDefault();e.returnValue="";}});
render();
