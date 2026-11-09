// Draft-only research notebook. This module never issues predictions or touches a network.
export const DRAFT_SCHEMA="idealab.psico.private-draft.v1";
const safeField=(value,max)=>typeof value==="string"&&value.trim().length<=max?value.trim():null;
export function validateDraft(input){
 if(!input||typeof input!=="object")throw Error("INVALID_DRAFT");
 const title=safeField(input.title,160),question=safeField(input.question,2000),hypothesis=safeField(input.hypothesis,3000);
 const method=safeField(input.method,3000),source=safeField(input.source,1500),notes=safeField(input.notes,4000);
 if(!title||title.length<3||!question||question.length<10||!hypothesis||hypothesis.length<10)throw Error("REQUIRED_RESEARCH_FIELDS");
 if(source){
   let url;try{url=new URL(source);}catch{throw Error("INVALID_SOURCE_URL");}
   if(url.protocol!=="https:"||url.username||url.password)throw Error("ONLY_HTTPS_SOURCES");
 }
 const target=safeField(input.target,100);
 return {title,question,hypothesis,method:method||"",source:source||"",target:target||"",notes:notes||""};
}
export function makeDraft(input,id,createdAt){
 const data=validateDraft(input);
 if(typeof id!=="string"||!/^WEB-[0-9a-f-]{12,48}$/i.test(id))throw Error("INVALID_ID");
 const time=new Date(createdAt);
 if(Number.isNaN(time.getTime())||time.getTime()>Date.now()+60000)throw Error("INVALID_DATE");
 return {schema:DRAFT_SCHEMA,id,created_at:time.toISOString(),state:"BORRADOR_NO_EMITIDO",
   issued:false,verified:false,...data};
}
export function validateNotebook(input){
 if(!input||input.schema!=="idealab.psico.private-notebook.v1"||!Array.isArray(input.drafts)||input.drafts.length>1000)throw Error("INVALID_NOTEBOOK");
 const ids=new Set();
 for(const item of input.drafts){
  if(item.schema!==DRAFT_SCHEMA||item.state!=="BORRADOR_NO_EMITIDO"||item.issued!==false||item.verified!==false)throw Error("UNVERIFIED_ENTRY");
  validateDraft(item);
  if(typeof item.id!=="string"||!/^WEB-[0-9a-f-]{12,48}$/i.test(item.id)||ids.has(item.id))throw Error("DUPLICATE_OR_BAD_ID");
  if(Number.isNaN(Date.parse(item.created_at)))throw Error("INVALID_TIMESTAMP");
  ids.add(item.id);
 }
 return structuredClone(input.drafts);
}
export function exportNotebook(drafts,at){
 validateNotebook({schema:"idealab.psico.private-notebook.v1",drafts});
 return JSON.stringify({schema:"idealab.psico.private-notebook.v1",exported_at:new Date(at).toISOString(),
   warning:"BORRADORES NO EMITIDOS. NO SON PREDICCIONES CERTIFICADAS NI COPIA DE CUSTODIA INSTITUCIONAL.",
   drafts},null,2)+"\n";
}
export function describeScientificFile(value){
 const type=Array.isArray(value)?"lista":typeof value;
 if(value===null||!["lista","object"].includes(type))throw Error("SCIENTIFIC_JSON_EXPECTED");
 const keys=Array.isArray(value)?[]:Object.keys(value).slice(0,14);
 const arrays=Array.isArray(value)?value.length: Object.values(value).filter(Array.isArray).reduce((n,arr)=>n+arr.length,0);
 return {kind:type,topLevelKeys:keys,visibleArrayEntries:arrays};
}

export function searchScientificObject(value,query,maxResults=40){
 const q=String(query??"").trim().toLowerCase();
 if(q.length<3||q.length>100||!Number.isInteger(maxResults)||maxResults<1||maxResults>100)throw Error("INVALID_SEARCH");
 if(value===null||typeof value!=="object")throw Error("SCIENTIFIC_JSON_EXPECTED");
 const results=[],stack=[{value,path:"$"}];
 let examined=0;
 while(stack.length&&examined<100000&&results.length<maxResults){
  const item=stack.pop();examined++;
  const v=item.value;
  if(v===null||typeof v!=="object"){
   const s=String(v);
   if(s.toLowerCase().includes(q))results.push({path:item.path,preview:s.slice(0,700)});
   continue;
  }
  const items=Array.isArray(v)?v.map((x,i)=>[String(i),x]):Object.entries(v);
  for(let i=items.length-1;i>=0;i--){
    const [key,child]=items[i];
    const path=Array.isArray(v)?item.path+"["+key+"]":item.path+"."+key.replace(/[\x00-\x1f]/g,"");
    if(String(key).toLowerCase().includes(q)&&results.length<maxResults){
      const preview=(child!==null&&typeof child==="object")?"Objeto estructurado":String(child);
      results.push({path,preview:preview.slice(0,700)});
    }
    stack.push({value:child,path});
  }
 }
 return {results,examined,truncated:stack.length>0||results.length>=maxResults};
}
