import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {loadProjectCatalog, validateProjectCatalog} from '../src/project-catalog.mjs';
const archive = JSON.parse(await readFile(new URL('../data/projects.json', import.meta.url)));
test('recovers four core tracks, three applications, documents and all relationships', () => {
  const data = validateProjectCatalog(archive);
  assert.equal(data.projects.length, 9);
  assert.equal(data.projects.filter(p => p.type === 'Aplicación de investigación').length, 3);
  assert.equal(data.projects.filter(p => p.documentation.vision).length, 8);
  assert.equal(data.relations.length, 14);
  assert.equal(data.relations.filter(r => r.target === 'prj-midas').length, 1);
});
test('fails closed on missing catalogue, missing core track or unresolved relation', async () => {
  await assert.rejects(loadProjectCatalog(async () => ({ok:false})), /UNAVAILABLE/);
  assert.throws(() => validateProjectCatalog({...archive, projects:[]}), /INCOMPLETE/);
  assert.throws(() => validateProjectCatalog({...archive, externalReferences:[]}), /INCOMPLETE|UNRESOLVED/);
});
test('loads local static data without credentials, preserving cancellation', async () => {
  const signal = new AbortController().signal;
  const data = await loadProjectCatalog(async (url, opts) => {
    assert.equal(url, './data/projects.json'); assert.equal(opts.credentials, 'omit');
    assert.equal(opts.signal, signal); return {ok:true, json:async () => archive};
  }, signal);
  assert.equal(data.status, 'HISTORICAL_CATALOGUE_RECOVERED');
});
test('public snapshot omits source identity paths, internal PRs and infrastructure',()=>{
 const raw=JSON.stringify(archive);
 for(const fragment of ['https://','.md','unapproved/source/path']) {
  assert.equal(raw.includes(fragment),false,'forbidden historical locator: '+fragment);
 }
 assert.equal(archive.currentOperationalStatusVerified,false);
 assert.equal(archive.prospectiveForecastIssued,false);
 assert.equal(archive.publicationScope,
  'SANITIZED_PUBLIC_HISTORICAL_SNAPSHOT_NOT_OPERATIVE_STATUS');
});
test('reject altered identity, document coverage, duplicate relations, dates and old identifiers',()=>{
 const duplicate=structuredClone(archive);
 duplicate.projects[1].id=duplicate.projects[0].id;
 assert.throws(()=>validateProjectCatalog(duplicate),/IDEAS_/);
 const extras=structuredClone(archive);
 extras.projects[0].documentation.keyDocs='unauthorized document';
 assert.throws(()=>validateProjectCatalog(extras),/IDEAS_/);
 const fake=structuredClone(archive);
 fake.projects[0].summary='See https://example.invalid/private';
 assert.throws(()=>validateProjectCatalog(fake),/IDEAS_/);
 const badDate=structuredClone(archive);
 badDate.projects[0].updatedAt='2026-02-30';
 assert.throws(()=>validateProjectCatalog(badDate));
 const duplicated=structuredClone(archive);
 duplicated.relations[1]=structuredClone(duplicated.relations[0]);
 assert.throws(()=>validateProjectCatalog(duplicated),/IDEAS_RELATION_DUPLICATE/);
 const claims=structuredClone(archive);
 claims.currentOperationalStatusVerified=true;
 assert.throws(()=>validateProjectCatalog(claims),/IDEAS_CATALOG_INVALID/);
});
