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

## Reproducibilidad

- Código: `scripts/audit_geo_ged20_21_coverage_revisions.py`.
- Pruebas sintéticas con denominador territorial, inversión de etiqueta y rechazo de versiones no registradas: `scripts/test_audit_geo_ged20_21_coverage_revisions.py`.
- Informe JSON verificado: `data/geo-ged-20-21-coverage-revisions.json`.
- CI dedicada: `.github/workflows/geo-ged-20-21-coverage-revisions.yml`; control obligatorio adicional en `.github/workflows/pages.yml`.
- No se publican eventos brutos, testimonios ni fuentes privadas. Ninguna probabilidad o alerta de GEO2027/GEO2028 cambia.

### Referencias oficiales

[Archivo de ediciones UCDP](https://ucdp.uu.se/downloads/olddw.html) · [GED20.1 Codebook](https://ucdp.uu.se/downloads/ged/ged201.pdf) · [GED21.1 Codebook](https://ucdp.uu.se/downloads/ged/ged211.pdf) · [Uppsala, anuncio de GED20.1 y primera inclusión de Siria, 16/06/2020](https://www.uu.se/en/department/peace-and-conflict-research/news/archive/2020-06-16-major-data-releases-from-ucdp).
