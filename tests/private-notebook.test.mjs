import test from "node:test";
import assert from "node:assert/strict";
import {makeDraft,validateDraft,validateNotebook,exportNotebook,describeScientificFile} from "../src/private-notebook.mjs";
const data={title:"Nuevo estudio",question:"¿Qué datos permitirían refutar este mecanismo?",hypothesis:"El mecanismo es falsable mediante datos externos.",method:"Comparación preregistrada",source:"https://www.census.gov/",notes:"Contrastar el calendario",target:"2027"};
test("creates a non-issued research draft",()=>{
 const draft=makeDraft(data,"WEB-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa","2026-11-09T11:00:00Z");
 assert.equal(draft.state,"BORRADOR_NO_EMITIDO");
 assert.equal(draft.issued,false);assert.equal(draft.verified,false);
 assert.deepEqual(validateNotebook({schema:"idealab.psico.private-notebook.v1",drafts:[draft]}),[draft]);
 assert.match(exportNotebook([draft],"2026-11-09T11:20:00Z"),/NO SON PREDICCIONES CERTIFICADAS/);
});
test("requires falsifiable research fields and HTTPS source",()=>{
 assert.throws(()=>validateDraft({...data,question:"corta"}),/REQUIRED_RESEARCH_FIELDS/);
 assert.throws(()=>validateDraft({...data,source:"http://example.com"}),/ONLY_HTTPS_SOURCES/);
 assert.throws(()=>validateDraft({...data,source:"https://person@example.com/"}),/ONLY_HTTPS_SOURCES/);
});
test("rejects duplicate IDs and any claim of issued forecasts",()=>{
 const a=makeDraft(data,"WEB-bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb","2026-11-09T11:00:00Z");
 assert.throws(()=>validateNotebook({schema:"idealab.psico.private-notebook.v1",drafts:[a,a]}),/DUPLICATE_OR_BAD_ID/);
 assert.throws(()=>validateNotebook({schema:"idealab.psico.private-notebook.v1",drafts:[{...a,issued:true}]}),/UNVERIFIED_ENTRY/);
});
test("describes imports without leaking their content",()=>{
 assert.deepEqual(describeScientificFile({records:[1,2,3],meta:{schema:1}}),{kind:"object",topLevelKeys:["records","meta"],visibleArrayEntries:3});
 assert.throws(()=>describeScientificFile(null),/SCIENTIFIC_JSON_EXPECTED/);
});
