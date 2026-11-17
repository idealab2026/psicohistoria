# PSICOHISTORIA · GED histórico y compatibilidad con OrganizedViolenceCY

**Diseño: 17 de noviembre de 2026. Investigación de equivalencia de la medición, no nuevo pronóstico ni backtest.**

## Problema abierto

Los modelos GEO2027 y GEO2028 emplean la etiqueta binaria `sb_total_deaths_best >= 25`, estimada sobre la serie `UCDP OrganizedViolenceCY` por país (GWNO) y año. El estudio de 2014–2025 utilizó ediciones anuales mucho más recientes que algunos de los años simulados. **No es válido llamar a ese ejercicio predicción histórica emitida entonces.**

La [sección oficial UCDP de ediciones históricas](https://ucdp.uu.se/downloads/olddw.html) sí conserva versiones **GED 17.1, 18.1, 19.1, 20.1, 21.1 y 22.1**, anteriores a la edición OrganizedViolenceCY 23.1. UCDP GED es una **tabla de eventos letales individuales**; la tabla country-year es otra unidad de análisis construida a partir de esos eventos.

El [codebook UCDP GED 22.1](https://ucdp.uu.se/downloads/ged/ged221.pdf) identifica su edición como compilada en **2022** y registra una **extracción de datos el 27 de abril de 2022**. Esta fecha no prueba que un ZIP actualmente descargable con ese nombre tenga exactamente los mismos bytes que el archivo publicado en 2022. No confundir *fecha de extracción*, *año del codebook* y *fecha de publicación con hash sellado*.

## Hipótesis de la prueba de compatibilidad

La prueba que decide si los eventos permiten reconstruir la etiqueta original es **GED 23.1 agregado por país-año frente a OrganizedViolenceCY 23.1**, es decir, **la misma edición**. Los datos de 22.1 o 19.1 no deben compararse directamente con OrganizedViolenceCY 23.1 para afirmar equivalencia: en esa comparación se mezclan inevitablemente reglas de agregación y **revisiones entre ediciones**.

Las primeras descargas oficiales sometidas a SHA-256 son:

| Fuente | Edición | Unidad | Uso en este experimento |
|---|---|---|---|
| GED 19.1 | Archivo oficial 2019 | Evento | Muestra anterior para observar cambios de etiquetado y cobertura |
| GED 22.1 | Archivo oficial 2022 | Evento | Disponibilidad histórica anterior a OrganizedViolenceCY |
| GED 23.1 | Archivo oficial 2023 | Evento | Prueba de **equivalencia dentro de la misma edición** |
| OrganizedViolenceCY 23.1 | Archivo oficial 2023 ya fijado por SHA-256 | País-año | Variable original del modelo GEO y denominador de referencia |

Primero se valida que cada archivo GED contiene **exactamente un CSV** y campos `id`, `year`, `country_id`, `type_of_violence`, `best`. Se impide reutilizar IDs de evento, se comprueba el GWNO y se registran los tipos por separado. La variable `type_of_violence = 1` indica **conflicto estatal (*state-based*)**; `2` es violencia no estatal y `3` violencia unilateral. Mezclarlas produciría una pregunta distinta.

El diagnóstico preliminar calculado es:

`raw_GED_state_based_deaths(GWNO, año) = SUM(best) para eventos de type_of_violence=1`

Para comparar con la etiqueta binaria `>=25` se usan **exactamente los 196 GWNO originales**, con todos los años 2011–2022 para el puente mismo-vintage. Si un país-año carece de evento GED en esa edición, el **recuento bruto de eventos registrados** se codifica como 0 en esa comparación, pero **no se infiere que no hubiera violencia real**.

## Qué valida el experimento, y qué no

Se publican, en el puente mismo-vintage y por año, número de recuentos exactamente idénticos, desacuerdos de la clasificación `>=25`, diferencias absolutas, casos extremos y cobertura. Los archivos GED 19.1/22.1 se cotejan tanto con GED 23.1 como, **solo a efectos descriptivos**, con la serie OrganizedViolenceCY 23.1 **de otra edición**. Esta última comparación no es prueba de reconstrucción de la variable original.

**Regla de seguridad científica:** incluso si la suma directa de GED 23.1 coincidiera exactamente con OrganizedViolenceCY 23.1 en los 2.352 país-años, **no se sustituirá automáticamente** la definición prospectiva de GEO. Será necesario auditar la regla de inclusión UCDP para díadas que alcanzan el umbral de 25 víctimas y la compatibilidad territorial/temporal entre las ediciones anteriores. El [codebook UCDP OrganizedViolenceCY 26.1](https://ucdp.uu.se/downloads/organizedviolencecy/UCDP_OrganizedViolenceCY_Codebook_261.pdf) documenta que algunas díadas solo entran en la base una vez que cruzan el umbral anual y pueden figurar con menos de 25 víctimas en años posteriores. Los ceros en la tabla no equivalen automáticamente a ausencia de violencia.

**No es una prueba de forecasting**: no se entrenan modelos, no se recalculan probabilidades emitidas y no se utilizan resultados oficiales de 2027. La comparación de GED19.1 contra GED23.1 tampoco aporta años adicionales independientes.

## Reproducibilidad y controles

- Descubrimiento de rutas reales directamente desde el catálogo oficial y rechazo de enlaces externos.
- Descarga de los ZIP oficiales, SHA-256 exacto, conteo de eventos y composición por tipos, con validación de integridad y de IDs únicos.
- Reconciliación de OrganizedViolenceCY23.1 con su SHA-256 ya fijado en el proyecto.
- Pruebas adversariales sintéticas que impiden mezclar los tipos 1, 2 y 3; rechazan ZIP corruptos, IDs duplicados y columnas faltantes.
- JSON público solo con agregaciones, sin republicar registros completos de eventos, nombres de participantes ni fuentes privadas.
- CI dedicada y control de que ninguna predicción o alerta prospectiva existente ha cambiado.

Código: `scripts/audit_geo_legacy_ged_countryyear_bridge.py`.
Pruebas: `scripts/test_audit_geo_legacy_ged_countryyear_bridge.py`.
Informe determinista: `data/geo-ged-old-vintage-countryyear-feasibility.json`.

## Resultados de las primeras tres descargas oficiales

Se han descargado las ediciones GED 19.1, 22.1 y 23.1 del catálogo histórico oficial y verificado su SHA-256. Se han procesado **152.616, 293.634 y 316.818 eventos**, respectivamente, sin reutilizar IDs de evento ni mezclar violencia estatal (tipo 1) con violencia no estatal (tipo 2) o unilateral (tipo 3).

**Prueba de identidad entre fuentes de la MISMA edición:** GED23.1, filtrado por `type_of_violence == 1` y agregado como `SUM(best)`, reproduce **exactamente 2.352 de 2.352 valores** `sb_total_deaths_best` de OrganizedViolenceCY23.1 en los 196 GWNO originales entre 2011 y 2022. El desacuerdo numérico total es **cero** y hay **cero cambios** de etiqueta en `>=25`. La coincidencia es un resultado comprobado; no se presupuso en el protocolo.

| Fuente GED antigua vs. GED23.1 | Países × años | Diferencias en etiqueta ≥25 |
|---|---:|---:|
| GED22.1, años comunes 2011–2021 | 2.156 | **0** |
| GED19.1, años comunes 2011–2018 | 1.568 | **17** |

En GED22.1 hay cambios en los **recuentos absolutos** frente a GED23.1, pero ninguno cruza el umbral binario `>=25` en la cohorte y años comparados. La serie histórica GED19.1 muestra 17 discrepancias binarias, **de las que ocho corresponden al GWNO 652 (Siria)**.

### Advertencia esencial: exclusión territorial de Siria en GED19.1

La [comunicación oficial de la Universidad de Uppsala del 16/06/2020](https://www.uu.se/en/department/peace-and-conflict-research/news/archive/2020-06-16-major-data-releases-from-ucdp) afirma expresamente que **GED20.1 fue la primera edición que incluyó Siria** en la serie GED global. GED19.1, por tanto, no puede interpretarse como una medición global homogénea de 2011–2018 para Siria: en su recuento estatal aparecen **cero eventos en la cohorte desde 2011 a 2018**, mientras que GED23.1 registra una etiqueta activa en esos ocho años. Son **ausencias por cobertura**, no ocho resultados negativos de violencia estatal.

La comparación pública distingue las **ocho discrepancias causadas por la exclusión territorial** de las **nueve restantes** (que podrían responder a revisiones, mejoras de cobertura o cambios de codificación). No se imputan ceros de GED19.1 como observaciones negativas válidas para entrenar y puntuar GEO.

### Hashes de los archivos oficiales

- GED19.1 ZIP: `58a640f82abe9b67090ded37f3163ca6839b36d737fddaacde95763b459a018f`
- GED22.1 ZIP: `1741045a14a59e2ddbe9de4a190a7ef5b68d60d57be7e94178aff2e926a59f0d`
- GED23.1 ZIP: `9aa082f9e1f62da5ea3245c39b1cee45daab6dc8b3a17fb0f0cdae9ba13ce6f7`
- GED22.1 PDF: `2e5020a58e8287c18bc033922cb32b6820c8a3a95f4fe98583b5c86774f58a8c`
- OrganizedViolenceCY23.1 ya fijado en el proyecto: `6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff`

Estas huellas autentican los **bytes oficiales descargables ahora**; no demuestran que el archivo fuera descargable con exactamente esos bytes en la fecha que su codebook cita.

**Conclusión intermedia:** existe un puente aritmético exacto GED23.1→OrganizedViolenceCY23.1 para el indicador de GEO en esta cohorte. La viabilidad retrospectiva de versiones anteriores depende también de cobertura, conservación de las reglas de inclusión y trazabilidad temporal. No se ha autorizado una nueva serie histórica de entrenamiento ni una sustitución de las predicciones prospectivas.

**Criterio para avanzar:** identificar la causa de cualquier desigualdad de etiqueta `>=25` dentro de GED23.1 y OrganizedViolenceCY23.1 antes de plantear un backtest con GED22.1/19.1. Una coincidencia parcial no equivale a identidad de variable ni a demostración de habilidad predictiva prospectiva.
