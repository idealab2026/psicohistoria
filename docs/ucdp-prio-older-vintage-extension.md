# PSICOHISTORIA — Extensión de ediciones históricas UCDP/PRIO 20.1–22.1

**12 de noviembre de 2026. Investigación de procedencia, no emisión de predicciones.**

## Una limitación crucial del proyecto

La fuente principal GEO-2027 es **UCDP Country-Year Dataset on Organized Violence**, etiquetada por **25 muertes de violencia organizada estatal**. El histórico oficial de ese producto solo contiene las ediciones **23.1, 24.1, 25.1 y 26.1**. El API también distingue explícitamente este producto de la serie UCDP/PRIO Armed Conflict, que ofrece más ediciones históricas.

No se puede añadir sin más UCDP/PRIO 20.1–22.1 como si fueran las mismas etiquetas GEO: ACD tiene unidad **conflicto-año** y recoge conflictos armados de un tipo determinado; no proporciona una tabla de 196 países-año, incluyendo sus casos negativos, para el indicador de muertes de `OrganizedViolenceCY`. Sus datos son aptos para otra línea de investigación de **presencia de conflictos interestatales/intraestatales**, no para certificar la calibración o dependencia de GEO-2027.

Fuentes institucionales de referencia: <https://ucdp.uu.se/downloads/olddw.html> y <https://ucdp.uu.se/apidocs/index.html>.

## Objetivo de esta iteración

Abrir la línea **ACD intrastate conflict incidence (country-year presence)** verificando las ediciones antiguas:

- UCDP/PRIO **20.1**, corte de observaciones 2019.
- UCDP/PRIO **21.1**, corte 2020.
- UCDP/PRIO **22.1**, corte 2021.
- UCDP/PRIO **23.1**, corte 2022 (ZIP y SHA-256 ya fijados en el proyecto).
- UCDP/PRIO **25.1**, corte 2024 (ZIP y SHA-256 ya fijados).

El script `scripts/diagnose_ucdp_prio_older_vintages.py` debe obtener los archivos exclusivamente de `ucdp.uu.se` mediante HTTPS; solo admite ZIP oficiales con una única tabla CSV y los campos originales `year`, `type_of_conflict`, `gwno_a`, `gwno_loc` y `conflict_id`. Mantiene únicamente conflictos **intraestatales** tipo 3/4, exige códigos de Gobierno y localización simples e iguales y rechaza duplicados. Desagrupa/agrupa registros de *conflict-year* a presencias de *country-year*; no convierte la ausencia de un registro en un cero sin disponer de un universo externo fechado.

El protocolo para cada par de ediciones consecutivas compara **exactamente los mismos años históricos observables en la primera edición** y cuantifica apariciones y desapariciones de pares país-año con conflicto intraestatal registrado. Estos cambios entre ediciones **no son transiciones históricas** ni revisiones del número de muertes del GEO, sino cambios de codificación de fuentes del endpoint ACD.

## Certificación en dos fases

**Fase A, descubrimiento:** descargar 20.1, 21.1 y 22.1 y verificar formato/semántica. Obtener sus SHA-256 exactos, tamaños, años límite y distribución de registros por tipo. En esta fase deben aparecer explícitamente como **NO PINNED** y la salida se marca `SOURCE_DISCOVERY_PROVISIONAL_NOT_FOR_MODEL_EVALUATION`. Queda prohibido inferir valor predictivo o usar las etiquetas como histórico «certificado».

**Fase B, fijación:** introducir en código cada SHA-256 obtenido en los ZIP reales, volver a descargarlos y verificar sus hashes, repetir las auditorías de estructura, cobertura y revisiones, y almacenar un informe agregado que se reproduce en GitHub Actions **byte a byte**. Tras superar toda la auditoría se podrá integrar una fuente histórica ACD adicional.

Los años de publicación de cada edición se infieren de su nombre; **no existe certificación notarial independiente de la fecha real de primera publicación**. Toda extensión posterior de predicción histórica debe utilizar un protocolo específico de ACD, una cohorte de países con casos negativos verificables y estricta separación de etiquetas posteriores. Ninguna mejora histórica de ACD podrá atribuirse retroactivamente a GEO-2027.

**Integridad:** no se cambia ningún vector de GEO-2027, GEO shadow, las 15 alertas, NEWCONF-2027 ni sus compromisos públicos; siguen sin existir observaciones finales de 2027.
