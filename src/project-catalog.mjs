/**
 * Publicly scoped institutional projection of the original research ideas.
 * Reconstructed wording and new identifiers intentionally sever links to
 * private records; a public catalog is never an operational certification.
 */
const expected=new Set(["lab-core","track-structural","track-forecast","track-agents",
 "track-meta","application-agenda","application-transmission",
 "application-radar","lab-public"]);
const restricted=[
 /github\.com\/(?!idealab2026\b)/i,/[\w.+-]+@[\w.-]+\.[a-z]{2,}/i,
 /\/Users\//i,/\/home\//i,/docs\/psicohistoria/i,
 /(?:PR|issue)\s*#\s*\d+/i,/psicoexperimentos/i,
 /segundo[\s_-]*cerebro/i,/mayordomo/i,/mamg97/i,
 /(?:\bworkers\.dev\b|cloudflare)/i,
 /(?:https?:\/\/)[^\s"']+/i
];
const exact=(obj,keys)=>obj&&typeof obj==="object"&&!Array.isArray(obj)&&
 Object.keys(obj).sort().join("|")===keys.slice().sort().join("|");
export function validateProjectCatalog(data){
 if(data?.schema!=="idealab.psico.public-project-catalog.v1"||
    data.ok!==true||data.status!=="PUBLIC_INSTITUTIONAL_PROJECTION"||
    data.forecastIssued!==0||data.verifiedProspectiveResults!==0||
    !Array.isArray(data.projects)||data.projects.length!==9||
    !Array.isArray(data.relations)||data.relations.length!==14||
    !Array.isArray(data.externalReferences)||data.externalReferences.length!==1||
    !exact(data.coverage,["projects","coreTracks","applications","documentationRecords","relations"])||
    [data.coverage.projects,data.coverage.coreTracks,data.coverage.applications,
     data.coverage.documentationRecords,data.coverage.relations].join(",")!=="9,4,3,8,14"||
    !exact(data.privacy,["sourceIdsReused","internalPathsIncluded",
                         "historicPrivateNotesIncluded","independentPublication"])||
    data.privacy.sourceIdsReused!==false||
    data.privacy.internalPathsIncluded!==false||
    data.privacy.historicPrivateNotesIncluded!==false||
    data.privacy.independentPublication!==true)
   throw Error("PUBLIC_PROJECT_CATALOG_INVALID");
 const ids=new Set();
 let tracks=0,apps=0,docs=0;
 for(const p of data.projects){
  if(!exact(p,["id","name","category","area","subtitle","summary",
                "documentation","stageNote","liveOperationalVerification"])||
     !expected.has(p.id)||ids.has(p.id)||p.liveOperationalVerification!==false||
     !["Programa","Vertiente","Aplicación","Plataforma"].includes(p.category)||
     [p.name,p.area,p.subtitle,p.summary,p.stageNote].some(x=>typeof x!=="string"||
       x.trim()!==x||x.length<5||x.length>500))throw Error("PUBLIC_PROJECT_ENTRY_INVALID");
  if(p.category==="Vertiente")tracks++;
  if(p.category==="Aplicación")apps++;
  if(p.documentation!==null){
   if(!exact(p.documentation,["vision","scope","method","validation","limitations"])||
      Object.values(p.documentation).some(x=>typeof x!=="string"||x.length<15||x.length>500))
     throw Error("PUBLIC_PROJECT_DOCUMENTATION_INVALID");
   docs++;
  }
  ids.add(p.id);
 }
 if(ids.size!==9||tracks!==4||apps!==3||docs!==8||
    data.projects.filter(p=>p.category==="Programa").length!==1||
    data.projects.filter(p=>p.category==="Plataforma").length!==1||
    data.projects.find(p=>p.id==="lab-public").documentation!==null)
   throw Error("PUBLIC_PROJECT_COVERAGE_INCOMPLETE");
 const references=data.externalReferences;
 if(!exact(references[0],["id","name","scope"])||
    references[0].id!=="ext-midas"||references[0].name!=="MIDAS"||
    references[0].scope.length<15)throw Error("PUBLIC_PROJECT_EXTERNAL_REFERENCE_INVALID");
 const seen=new Set();
 for(const r of data.relations){
  if(!exact(r,["source","target","type","description"])||
     !ids.has(r.source)||r.source===r.target||
     !(ids.has(r.target)||r.target==="ext-midas")||
     typeof r.type!=="string"||!/^[A-Z_]{5,42}$/.test(r.type)||
     typeof r.description!=="string"||r.description.length<10||
     seen.has(r.source+"→"+r.target+"→"+r.type))
    throw Error("PUBLIC_PROJECT_RELATIONS_INVALID");
  seen.add(r.source+"→"+r.target+"→"+r.type);
 }
 if(data.relations.filter(r=>r.target==="ext-midas").length!==1||
    data.relations.filter(r=>r.type==="PERTENECE_A").length!==6)
   throw Error("PUBLIC_PROJECT_RELATIONS_INCOMPLETE");
 const raw=JSON.stringify(data);
 if(raw.length>23000||restricted.some(rx=>rx.test(raw))||
    /[A-Za-z]:\\Users\\/i.test(raw))throw Error("PUBLIC_PROJECT_PRIVACY_REJECTED");
 return data;
}
export async function loadProjectCatalog(fetcher=globalThis.fetch,signal){
 if(typeof fetcher!=="function")throw Error("PUBLIC_PROJECT_FETCH_UNAVAILABLE");
 const response=await fetcher("./data/projects.json",{
  cache:"no-store",credentials:"omit",signal
 });
 if(!response?.ok)throw Error("PUBLIC_PROJECT_CATALOG_UNAVAILABLE");
 return validateProjectCatalog(await response.json());
}
