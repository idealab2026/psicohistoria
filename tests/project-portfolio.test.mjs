import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {validateProjectCatalog} from "../src/project-catalog.mjs";
import {renderHistoricalProjectPortfolio} from "../src/project-portfolio.mjs";
const data=validateProjectCatalog(JSON.parse(await readFile(
 new URL("../data/projects.json",import.meta.url),"utf8")));
test("Nine independent public projects and all fourteen relationships render as structured, accessible cards",()=>{
 const html=renderHistoricalProjectPortfolio(data);
 for(const project of data.projects){
  assert.ok(html.includes('id="portfolio-'+project.id+'"'),project.id);
  assert.ok(html.includes(project.name),project.id);
 }
 for(const text of ["Cuatro vertientes","Tres aplicaciones","14","9",
  "Ideas y aplicaciones","Metodología y conexiones",
  "identificadores nuevos","No certifica operación actual"]){
  assert.ok(html.includes(text),text);
 }
 assert.equal((html.match(/class="portfolio-card"/g)||[]).length,9);
 assert.equal((html.match(/<li><span>/g)||[]).length,14);
 assert.equal((html.match(/<details>/g)||[]).length,9);
});
test("Public projection never displays original internal IDs, archived paths, private dates or false outcomes",()=>{
 const html=renderHistoricalProjectPortfolio(data);
 assert.equal(html.includes("2026-10-16"),false);
 assert.equal(html.includes("PR #"),false);
 assert.equal(html.includes("source/path"),false);
 assert.equal(html.includes("actualizado en origen"),false);
 assert.ok(html.includes("no activan operaciones"));
 assert.ok(html.includes("no verifica"));
});
test("All dynamic descriptions are escaped and cannot introduce malicious markup",()=>{
 const altered=structuredClone(data);
 altered.projects[0].summary='<img src=x onerror=alert(1)>';
 altered.relations[0].description='<svg onload=alert(2)>';
 const html=renderHistoricalProjectPortfolio(altered);
 assert.ok(html.includes("&lt;img src=x onerror=alert(1)&gt;"));
 assert.ok(html.includes("&lt;svg onload=alert(2)&gt;"));
 assert.equal(html.includes("<svg onload"),false);
 assert.equal(html.includes("<img src=x onerror"),false);
});
test("No catalog means visible source failure, never success with zero projects",()=>{
 const html=renderHistoricalProjectPortfolio(null);
 assert.ok(html.includes("Catálogo no disponible"));
 assert.ok(html.includes("No se generan proyectos de respaldo"));
 assert.equal(html.includes('id="portfolio-'),false);
});
