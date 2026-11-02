const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const expected=[21,23,164,1177,57,174,13,2,2,9,193];
export function verifyScientificArchive(doc){
 if(doc?.schema!=="idealab_scientific_workbook_v1"||!Array.isArray(doc.tables)||doc.tables.length!==11)throw Error("Archivo científico inválido");
 for(const [i,t] of doc.tables.entries()){
  if(typeof t.name!=="string"||!t.header||!Array.isArray(t.rows)||t.records!==expected[i]||t.rows.length!==expected[i])throw Error("Tabla científica incompleta");
  for(const row of [t.header,...t.rows])for(const [key,value]of Object.entries(row)){
   if(!/^[A-Z]+[1-9][0-9]*$/.test(key)||!(typeof value==="string"||Array.isArray(value)&&value.length===2&&value.every(x=>typeof x==="string")))throw Error("Celda científica inválida");
   if(/docs\.google\.com|drive\.google\.com|workers\.dev|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/i.test(JSON.stringify(value)))throw Error("Referencia privada en archivo");
  }
 }
 return {tables:11,records:expected.reduce((a,b)=>a+b,0),predictions:1177,verifiedOutcomes:0};
}
export function scientificArchiveTable(doc,{table=0,query="",page=0}={}){
 verifyScientificArchive(doc);const t=doc.tables[table];if(!t)throw Error("Tabla desconocida");
 const q=String(query).trim().toLocaleLowerCase("es");const rows=t.rows.filter(r=>!q||JSON.stringify(r).toLocaleLowerCase("es").includes(q));
 const pages=Math.max(1,Math.ceil(rows.length/30)),selected=Math.min(Math.max(0,page),pages-1);
 const columns=Object.keys(t.header).map(k=>k.replace(/[0-9]+$/,""));
 const cell=(row,col)=>{const k=Object.keys(row).find(k=>k.replace(/[0-9]+$/,"")===col);const v=row[k];return Array.isArray(v)?v[0]+" · fórmula: "+v[1]:v??"";};
 return {count:rows.length,page:selected,pages,html:'<div class="archive-scroll" tabindex="0" aria-label="Tabla científica con desplazamiento horizontal"><table><thead><tr>'+columns.map(c=>'<th scope="col">'+esc(cell(t.header,c))+'</th>').join("")+'</tr></thead><tbody>'+rows.slice(selected*30,selected*30+30).map(row=>'<tr>'+columns.map(c=>'<td>'+esc(cell(row,c))+'</td>').join("")+'</tr>').join("")+'</tbody></table></div>'};
}
