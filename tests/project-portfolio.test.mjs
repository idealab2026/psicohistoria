import {test} from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {validateProjectCatalog} from "../src/project-catalog.mjs";
import {renderHistoricalProjectPortfolio} from "../src/project-portfolio.mjs";
const data=validateProjectCatalog(JSON.parse(await readFile(new URL("../data/projects.json",import.meta.url),"utf8")));
test("All nine archived projects and fourteen relationships are shown in the institutional portfolio",()=>{
 const html=renderHistoricalProjectPortfolio(data);
 for(const project of data.projects){
  assert.ok(html.includes('id="portfolio-'+project.id+'"'),project.id);
  assert.ok(html.includes(project.name),project.id);
 }
 for(const marker of ["Cuatro vertientes científicas","Tres aplicaciones",
  "14","8","Estado en archivo","Ficha científica y relaciones",
  "2026-10-16","estado histórico","No se transfieren código privado"])
  assert.ok(html.includes(marker),marker);
 assert.equal((html.match(/class="portfolio-card"/g)||[]).length,9);
 assert.equal((html.match(/<li><span>/g)||[]).length,14);
});
test("Historical status is not mistaken for live services or newly certified forecasts",()=>{
 const html=renderHistoricalProjectPortfolio(data);
 assert.ok(html.includes("Los estados no son una lectura operativa de hoy"));
 assert.ok(html.includes("no verifica avances posteriores"));
 assert.ok(html.includes("no una transferencia de posiciones"));
 assert.ok(!html.includes("internal_document.md"));
 assert.ok(!html.includes("unapproved/source/path"));
 assert.ok(!html.includes("internal-experiment-registry"));
});
test("Rendering escapes untrusted text instead of injecting markup or HTML events",()=>{
 const altered=structuredClone(data);
 altered.projects[0].summary='<img src=x onerror=alert(1)>';
 const html=renderHistoricalProjectPortfolio(altered);
 assert.ok(html.includes("&lt;img src=x onerror=alert(1)&gt;"));
 assert.equal(html.includes('<img src=x onerror'),false);
});
test("Missing catalog fails visibly, never renders zero projects as successful migration",()=>{
 const html=renderHistoricalProjectPortfolio(null);
 assert.ok(html.includes("Catálogo no disponible"));
 assert.ok(html.includes("No se reconstruyen proyectos"));
 assert.equal(html.includes("Nueve expedientes"),false);
});
