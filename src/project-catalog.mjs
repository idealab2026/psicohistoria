/**
 * IDEA LAB public, historical project catalogue.
 * Derived from recovered source only after explicit disclosure projection;
 * must not expose implementation paths, old identities or current activity.
 */
const EXPECTED_IDS=Object.freeze([
 "prj-psicohistoria",
 "prj-psico-cliodinamica","prj-psico-forecast",
 "prj-psico-agentes","prj-psico-metalab",
 "prj-psico-agenda","prj-psico-transmision","prj-psico-radar",
 "prj-idea-lab-sistemas-publico"
]);
const DOC_KEYS=["vision","objective","scope","currentState","milestones","rules"];
const PROJECT_KEYS=["id","name","alias","parentId","area","type","status",
 "priority","summary","docsStatus","nextAction","updatedAt","documentation"];
const RELATION_KEYS=["sourceProjectId","type","targetType","target","description"];
const REFERENCE_KEYS=["id","name","recordKind"];
// Public boundary: technical paths, addresses, emails and legacy source files
// are inadmissible regardless of owner identity. CI also applies separately
// configured private deny terms over every public repo file.
const DENY=/(?:https?:\/\/|[a-z0-9._%-]+@[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9_.-]+\.(?:md|py|ts|mjs)\b|(?:\.\.\/)|(?:[a-z_-]+\/){2,}|(?:^|[^\w])Worker(?:[^\w]|$))/i;
const sameKeys=(value,allowed)=>value&&typeof value==="object"&&!Array.isArray(value)&&
 Object.keys(value).every(x=>allowed.includes(x));
const str=(v,max=2200)=>typeof v==="string"&&v.trim().length>0&&v.length<=max;
const fail=code=>{throw Error("IDEAS_"+code)};
const verifiedDate=value=>{
 if(typeof value!=="string"||!/^\d{4}-\d\d-\d\d$/.test(value)||
  new Date(value+"T00:00:00Z").toISOString().slice(0,10)!==value)fail("DATE_INVALID");
};
export function validateProjectCatalog(data){
 if(data?.schema!=="idealab.psico.ideas.v1"||data.ok!==true||
    data.status!=="HISTORICAL_CATALOGUE_RECOVERED"||
    data.publicationScope!=="SANITIZED_PUBLIC_HISTORICAL_SNAPSHOT_NOT_OPERATIVE_STATUS"||
    data.currentOperationalStatusVerified!==false||
    data.prospectiveForecastIssued!==false||
    !Array.isArray(data.projects)||!Array.isArray(data.relations)||
    !Array.isArray(data.externalReferences)||!data.coverage||
    !str(data.notice)||!str(data.capturedAt,50))
  fail("CATALOG_INVALID");
 const p=data.projects;
 if(p.length!==9||data.relations.length!==14||
    data.externalReferences.length!==1||
    data.coverage.projects!==9||data.coverage.documentationRecords!==8||
    data.coverage.relations!==14||data.coverage.coreTracks!==4||
    data.coverage.applications!==3)fail("COVERAGE_INCOMPLETE");
 const ids=new Set(p.map(x=>x?.id));
 if(ids.size!==9||EXPECTED_IDS.some(id=>!ids.has(id)))
  fail("PROJECT_IDENTITY_INCOMPLETE");
 for(const entry of p){
  if(!sameKeys(entry,PROJECT_KEYS)||
     ["id","name","alias","parentId","area","type","status",
      "priority","summary","docsStatus","nextAction","updatedAt"].some(k=>!str(entry[k]))||
     !sameKeys(entry.documentation,DOC_KEYS))
   fail("PROJECT_SCHEMA");
  verifiedDate(entry.updatedAt);
  if(Object.values(entry.documentation).some(x=>!str(x,2600)))
   fail("DOCUMENTATION_INVALID");
  if(entry.id==="prj-psicohistoria"&&entry.parentId!=="prj-idea-lab")
   fail("PARENT_INVALID");
  if(entry.id!=="prj-psicohistoria"&&entry.parentId!=="prj-psicohistoria")
   fail("PARENT_INVALID");
 }
 const apps=p.filter(x=>x.type==="Aplicación de investigación");
 const docs=p.filter(x=>str(x.documentation.vision));
 if(apps.length!==3||docs.length!==8||docs.some(x=>DOC_KEYS.some(k=>!str(x.documentation[k]))))
   fail("TRACKS_OR_DOCS_INCOMPLETE");
 for(const id of EXPECTED_IDS.slice(1,5))if(!p.find(x=>x.id===id&&/^V[1-4] — /.test(x.name)))
   fail("CORE_TRACKS_INCOMPLETE");
 if(!sameKeys(data.externalReferences[0],REFERENCE_KEYS)||
    data.externalReferences[0].id!=="prj-midas"||
    data.externalReferences[0].recordKind!=="RELATION_TARGET_ONLY")
   fail("EXTERNAL_REFERENCE_INVALID");
 const relations=new Set();
 for(const rel of data.relations){
  if(!sameKeys(rel,RELATION_KEYS)||
     ["sourceProjectId","type","targetType","target","description"].some(k=>!str(rel?.[k]))||
     !ids.has(rel.sourceProjectId)||
     !(ids.has(rel.target)||rel.target==="prj-midas"))
    fail("RELATION_UNRESOLVED");
  const key=rel.sourceProjectId+"|"+rel.type+"|"+rel.target;
  if(relations.has(key))fail("RELATION_DUPLICATE");
  relations.add(key);
 }
 if(data.relations.filter(x=>x.target==="prj-midas").length!==1)
   fail("CROSS_PROJECT_RELATION_DRIFT");
 if(DENY.test(JSON.stringify(data)))fail("PRIVACY_DISCLOSURE_REJECTED");
 return data;
}
export async function loadProjectCatalog(fetcher=globalThis.fetch,signal){
 const response=await fetcher("./data/projects.json",{
  cache:"no-store",credentials:"omit",signal
 });
 if(!response?.ok)fail("CATALOG_UNAVAILABLE");
 return validateProjectCatalog(await response.json());
}
