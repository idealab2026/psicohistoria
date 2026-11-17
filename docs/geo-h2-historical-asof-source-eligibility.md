# PSICOHISTORIA · GEO H2 — Auditoría de disponibilidad **as-of** de fuentes (17/11/2026)

**Motivo:** corregir una confusión metodológica decisiva. Recortar un archivo UCDP publicado con posterioridad a `año <= origen` evita introducir observaciones de años futuros, **pero no deshace revisiones posteriores en los datos anteriores al origen**. Por tanto, doce años de cálculo histórico no equivalen a doce años de predicciones que pudieron emitirse entonces.

## Evidencia primaria oficial

El [catálogo histórico UCDP Organized Violence Country-Year](https://ucdp.uu.se/downloads/olddw.html) enumera las ediciones **23.1, 24.1 y 25.1** para ese conjunto, mientras que la [API UCDP](https://ucdp.uu.se/apidocs/index.html) muestra únicamente la edición actual 26.1 para ese recurso. La ausencia de versiones 22.1 o anteriores **en ese catálogo** no demuestra que no existieran otros conjuntos de datos de violencia UCDP: versiones antiguas de GED, ACD, Non-State y One-Sided Violence sí aparecen en el archivo, pero no son automáticamente intercambiables con `sb_total_deaths_best` agregado por **país-año** con las reglas de OrganizedViolenceCY.

El [codebook oficial 23.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_231.pdf) indica que fue **compilado y actualizado en 2023** y contiene observaciones hasta el 31/12/2022. El [codebook oficial 24.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_241.pdf) indica **compilación en 2024**, con observaciones hasta el 31/12/2023. UCDP indica que sus datos se publican normalmente en **junio o julio** en la [FAQ oficial](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/frequently-asked-questions), pero **no puede tomarse ese mes habitual como fecha exacta demostrada de publicación** de cada fichero ni como prueba de que los bytes hoy descargados ya existían entonces.

El nuevo programa descarga los dos PDF oficiales, calcula sus SHA-256, inspecciona **todas las versiones mencionadas en la sección exacta** del catálogo histórico y comprueba sus rutas contra las versiones de datos UCDP cuya integridad ya estaba fijada. La fecha de compilación citada en el PDF aporta evidencia de año, no una certificación independiente de publicación ni un sello temporal del archivo original.

## Regla de exclusión fijada

Para cada una de las 12 parejas origen-año objetivo del backtest retrospectivo 2014–2025, clasificar:

- **Codebook posterior al resultado**: archivo documentalmente posterior a ese año objetivo; inadmisible como evidencia de una fuente accesible antes del resultado.
- **Codebook del mismo año objetivo**: la fecha exacta de disponibilidad respecto al desenlace no está certificada; no puede afirmarse que se contara con esa edición antes.
- **Codebook de un año anterior al resultado**: es **temporalmente plausible** pero NO verifica el checksum del archivo existente entonces, la fecha exacta de disponibilidad ni una predicción emitida.
- **Fuente certificada en el momento del origen**: requiere registro temporal independiente de los datos, de las predicciones y de sus hashes. Esta auditoría no dispone de tales pruebas para ninguno de los doce orígenes simulados.

Ningún año se marca como prospectivo por el mero hecho de tener un codebook de un año anterior. La etiqueta principal de evaluación sigue siendo UCDP `sb_total_deaths_best >=25`; no se modifican probabilidades, alertas, parámetros ni predicciones.

## Resultado de aplicar el filtro a los datos publicados

| Bloque de años objetivo | Años | Observaciones país-año | Markov binario Brier | Markov 4 estados Brier | Δ cuatro estados − binario |
|---|---:|---:|---:|---:|---:|
| **2014–2022**: documento 23.1 fechado después del objetivo | 9 | 1.764 | 0,04909907 | **0,04517001** | −0,00392906 |
| **2023**: codebook 23.1 del mismo año | 1 | 196 | 0,03888156 | **0,03860437** | −0,00027720 |
| **2024–2025**: codebooks anteriores al resultado; sin hash histórico certificado | 2 | 392 | **0,04008406** | 0,04244933 | +0,00236527 |
| **2014–2025**, reconstrucción histórica total | 12 | 2.352 | 0,04674511 | **0,04416943** | −0,00257568 |

Agrupando los diez años que **no acreditan un codebook anterior al objetivo** (2014–2023), la ventaja descriptiva del modelo de cuatro estados es **−0,00356387** en Brier sobre **1.960 observaciones país-año**. El grupo cuyo codebook es de un año anterior al resultado es el de 2024–2025, que favorece al modelo binario original.

**Diagnóstico clave:** la inversión de signo detectada al pasar de los dos años recientes a los doce años retrospectivos procede del conjunto de años sin evidencia de una edición idéntica disponible antes de esos resultados. La inversión es real aritméticamente dentro del histórico reconstruido, pero su interpretación como mejora de predicción **no está justificada por la evidencia temporal**.

## Qué está demostrado y qué no

**Sí**: resultados aritméticos reproducidos con fuentes actuales firmadas por SHA-256, fechas de compilación de dos codebooks oficiales, compatibilidad del esquema país-año 23.1/24.1 y auditoría de trece variables de consistencia de los informes previos. Hay una clasificación inequívoca a escala de **año documental**, con los años futuros ausentes del entrenamiento.

**No**: que los archivos exactos de 2023/2024 descargables ahora hubiesen tenido esos mismos bytes al publicarse, que existiera una predicción pre-registrada en 2012–2023, ni que el resultado de 2014–2025 pruebe habilidad prospectiva.

Las ediciones antiguas UCDP GED [17.1–22.1](https://ucdp.uu.se/downloads/olddw.html) son una posible vía futura **para un experimento diferente**: tendrían que reagregarse explícitamente sus eventos, auditar el mapeo GWNO, el recuento `best` y todas las diferencias de cobertura respecto al conjunto OrganizedViolenceCY. **No se deben introducir como datos comparables sin reconstrucción y validación.**

## Reproducibilidad institucional

Código: `scripts/audit_geo_h2_historical_asof_sources.py`.

Pruebas: `scripts/test_audit_geo_h2_historical_asof_sources.py`.

Resultado fijado: `data/geo-h2-2014-2025-temporal-source-eligibility.json`.

Control continuo: workflow `geo-h2-historical-asof.yml` y dependencia bloqueante de `pages.yml`; el JSON debe coincidir **byte a byte** con el cálculo a partir de los informes archivados y los dos PDF oficiales, además de aprobar la auditoría de publicación de IDEA LAB.

**Límite de privacidad:** todos los repositorios, documentación y metadatos son institucionales de IDEA LAB. No se añade ni referencia ninguna identidad o repositorio personal.
