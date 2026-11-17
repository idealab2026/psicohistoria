# PSICOHISTORIA · GED 20.1/21.1 — revisión histórica y cobertura territorial

**Diseño anterior a los resultados de este experimento: 17 de noviembre de 2026.** No emite predicciones ni reemplaza ninguna evaluación de GEO2027/GEO2028.

## Pregunta e hipótesis refutable

La auditoría anterior [GED19.1 / GED22.1 / GED23.1](geo-ged-legacy-countryyear-bridge.md) demostró que el agregado de eventos estatales `type_of_violence == 1`, `SUM(best)` por GWNO y año reproduce **2.352/2.352** recuentos de `sb_total_deaths_best` de OrganizedViolenceCY 23.1 (misma versión). La edición GED19.1 produjo 17 desacuerdos de clasificación `>=25` respecto a GED23.1 durante 2011–2018, **8 relativos a Siria, ausente por cobertura**.

Las [ediciones GED históricas del archivo UCDP](https://ucdp.uu.se/downloads/olddw.html) contienen también GED 20.1 y GED 21.1. UCDP describe específicamente la incorporación de Siria a GED20.1 como la primera cobertura nacional completa de su serie histórica. El [codebook GED20.1](https://ucdp.uu.se/downloads/ged/ged201.pdf) se compiló en 2020; documenta extracción del **7 de abril de 2020** y registra eventos hasta 2019. El [codebook GED21.1](https://ucdp.uu.se/downloads/ged/ged211.pdf) se compiló en 2021, documenta extracción el **8 de abril de 2021** y registra eventos hasta 2020.

**La hipótesis:** la transición GED19.1→GED20.1 incluye un cambio **estructural de cobertura de Siria**, distinto de las revisiones de los países que ambas ediciones registraban. Las ediciones GED20.1→GED21.1→GED22.1→GED23.1 permiten medir revisiones de las etiquetas sobre la misma cohorte fija, sin interpretarlas como muestras nuevas.

## Diseño

- **Cinco fuentes originales UCDP:** GED19.1, 20.1, 21.1, 22.1 y 23.1, con ZIP oficiales recuperados de enlaces publicados en el catálogo de UCDP. Se exigen SHA-256, esquema de eventos, IDs únicos y separación de los tres tipos de violencia.
- **Cohorte congelada:** 196 GWNO del GEO2027 original, 2011 hasta el último año registrado por la edición antigua de cada pareja. Toda versión se compara en los **mismos países y años comunes**, sin extrapolar resultados de 2020/2021 hacia años que no conocían.
- **Pares consecutivos:** 19.1→20.1 (2011–2018), 20.1→21.1 (2011–2019), 21.1→22.1 (2011–2020), 22.1→23.1 (2011–2021). Controles adicionales 20.1→23.1 y 21.1→23.1.
- **Indicador:** suma de fallecimientos `best` de eventos estatales (`type_of_violence=1`) por GWNO×año; binario `>=25`. No mezclar unilateral y no estatal.
- **Separación territorial:** GED19.1 **no contiene Siria**. Para 19.1→20.1 se publica el resultado ingenuo de considerar esas ocho filas como ceros **solo para cuantificar el error**, pero se excluyen del denominador científico y se marcan explícitamente como *no observadas*. GED20.1 sí incorpora Siria. El denominador correcto de 2011–2018 es **195 países × 8 años = 1.560**, no 196×8.
- **Trazabilidad temporal:** los codebooks indican **fecha de extracción**, no prueban un sello temporal independiente de las versiones ZIP exactas ni que los modelos históricos hubieran emitido predicciones antes de los resultados. No se calcularán nuevos Brier ni se afirmará habilidad prospectiva.

## Variables de salida

Para cada comparación se publica el número exacto de país-años comparables, recuentos de fallecidos idénticos, revisiones numéricas, cambios de etiqueta por país-año y año, número de activos por edición, y cambios relativos a Siria. Todos los pares comparten países y años; **no son evaluaciones independientes**. El resultado incluye las huellas de los cinco archivos ZIP, los PDF GED20.1/21.1 y la confirmación del informe original de 23.1.

**Precaución:** que GED23.1 reproduzca OrganizedViolenceCY23.1 no demuestra equivalencia automática de GED20.1/21.1 con el mismo resultado de otra edición, ni convierte una ausencia de evento en certeza de paz. Los cambios entre versiones son una mezcla de revisión editorial, disponibilidad/cobertura y posible definición revisada. Donde falta una fuente no se imputan ceros.

## Resultados reales reconstruidos desde las fuentes oficiales

Se han recuperado y verificado las cinco ediciones GED por SHA-256, además de ambos codebooks de 2020 y 2021. GED20.1 contiene **225.385 eventos** (hasta 2019), y GED21.1 contiene **261.864 eventos** (hasta 2020). Se utiliza exclusivamente type_of_violence=1 para la variable original de violencia estatal.

| Ediciones comparadas y años comunes | País-años comparables | Recuentos best distintos | Etiquetas >=25 distintas |
|---|---:|---:|---:|
| GED19.1 → GED20.1, 2011–2018, **sin Siria** | **1.560** | 45 | **2** |
| GED20.1 → GED21.1, 2011–2019 | 1.764 | 91 | **1** |
| GED21.1 → GED22.1, 2011–2020 | 1.960 | 93 | **6** |
| GED22.1 → GED23.1, 2011–2021 | 2.156 | 64 | **0** |
| GED20.1 → GED23.1, 2011–2019 (control) | 1.764 | 137 | **7** |
| GED21.1 → GED23.1, 2011–2020 (control) | 1.960 | 117 | **6** |

**Corrección Siria, GWNO 652.** GED19.1 no cubre Siria: hay ocho observaciones país-año no registradas entre 2011–2018. Tomarlas equivocadamente como cero observado daría **10 cambios** de etiqueta 19.1→20.1 sobre 1.568 filas. La comparación válida separa esas ocho filas estructuralmente ausentes, emplea **1.560 filas comparables** y arroja **solo 2 cambios**. Una fuente sin cobertura no aporta una etiqueta negativa de violencia.

Los dos cambios restantes de GED19.1→20.1 son GWNO **541 (2014, 21→30 fallecidos)** y GWNO **540 (2016, 18→25)**. El cambio 20.1→21.1 es GWNO **630 (2015, 24→25)**. Los seis cambios 21.1→22.1 corresponden a GWNO **616** (2013, 2014, 2015), GWNO **482** (2015, 2017) y GWNO **670** (2017). Todos son cambios de inactivo a activo bajo la etiqueta central >=25. Las diferencias se deben estudiar como **revisiones entre ediciones**, no como predicciones acertadas o fallidas.

La ausencia de cambios de etiqueta 22.1→23.1 coexiste con **64 recuentos absolutos diferentes**. Los contrastes adicionales con 23.1 contienen años y países solapados; no se pueden sumar como evaluaciones independientes.

### SHA-256 oficiales fijados para la reproducción

- GED20.1 ZIP: 5e35b74f52dc67a18aabfab86f69655c847e87320684662a6112dec46d65111f
- GED21.1 ZIP: 2cd62e39db0f49b784ecd1d48c364191c78afc9d5fb1bd9f6b6dda55dcd59afd
- GED20.1 PDF: 964becfa74e56e9217c123d059a6e4156037750dbaadd4b4e5a25de2c990e03a
- GED21.1 PDF: 4d1c6ab95462e8bee2c6a4e501fef7b5a5cde6c0e0cd1064bb5c8d3d3c7ab80c

Se verifica también el SHA de GED19.1/22.1/23.1 contra el informe original de la PR #110. Estas huellas prueban reproducibilidad de los bytes descargados en la auditoría, **no un sello de tiempo de publicación original**.

### Próxima frontera metodológica

Para entrenar retrospectivamente con GED anterior a OrganizedViolenceCY será necesario definir un conjunto GWNO con cobertura acreditada por edición, etiquetar explícitamente la exclusión territorial de Siria en 19.1, confirmar cobertura de los demás países y registrar el desfase entre origen histórico, extracción, publicación de la edición y obtención del ZIP original. La prueba GED23.1→OrganizedViolenceCY23.1 sigue siendo el único puente exacto a igual edición de GED/CY ya demostrado.

No se autorizan nuevos resultados prospectivos, reentrenamiento de modelos registrados ni sustitución del indicador original por este experimento de revisión.

## Reproducibilidad

- Código: `scripts/audit_geo_ged20_21_coverage_revisions.py`.
- Pruebas sintéticas con denominador territorial, inversión de etiqueta y rechazo de versiones no registradas: `scripts/test_audit_geo_ged20_21_coverage_revisions.py`.
- Informe JSON verificado: `data/geo-ged-20-21-coverage-revisions.json`.
- CI dedicada: `.github/workflows/geo-ged-20-21-coverage-revisions.yml`; control obligatorio adicional en `.github/workflows/pages.yml`.
- No se publican eventos brutos, testimonios ni fuentes privadas. Ninguna probabilidad o alerta de GEO2027/GEO2028 cambia.

### Referencias oficiales

[Archivo de ediciones UCDP](https://ucdp.uu.se/downloads/olddw.html) · [GED20.1 Codebook](https://ucdp.uu.se/downloads/ged/ged201.pdf) · [GED21.1 Codebook](https://ucdp.uu.se/downloads/ged/ged211.pdf) · [Uppsala, anuncio de GED20.1 y primera inclusión de Siria, 16/06/2020](https://www.uu.se/en/department/peace-and-conflict-research/news/archive/2020-06-16-major-data-releases-from-ucdp).
