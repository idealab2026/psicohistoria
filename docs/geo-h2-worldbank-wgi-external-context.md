# PSICOHISTORIA — Contraste institucional externo con WGI

**Estudio registrado el 18/11/2026.** Se incorpora un indicador producido por otra institución, los Worldwide Governance Indicators del Banco Mundial, para identificar si la intensidad de violencia organizada recogida por UCDP presenta alguna concordancia contextual con las percepciones de estabilidad política.

## La diferencia de constructos es obligatoria

- **UCDP OrganizedViolenceCY**, edición oficial 26.1: número anual de fallecidos de violencia organizada (mejor estimación), recodificados como evento activo de intensidad ≥25, entre otras categorías. Cobertura de entrenamiento de 199 países GWNO.
- **Banco Mundial, Political Stability, GOV_WGI_PV_EST**: percepción compuesta de la estabilidad del poder político y de riesgos de desestabilización por violencia u otros medios. Valores elevados implican mayor estabilidad percibida. **No cuenta muertes, no se diseña como una anotación independiente de los mismos eventos UCDP y puede incluir fuentes secundarias con dependencia informativa.**

No se suman ambas medidas ni se consideran etiquetas equivalentes. No se utiliza WGI para reestimar la matriz de errores `P(T verdadera|O observada)`, que sigue sin estar identificada.

La API oficial de indicadores es `https://api.worldbank.org/v2/country/all/indicator/GOV_WGI_PV_EST?format=json&per_page=20000&date=2012%3A2025`. Se valida el identificador del indicador y se conserva la huella SHA256 de la serie numérica normalizada. Si la API revisa los datos, la reproducción falla hasta que se evalúe la nueva versión; no se mezclan sin trazabilidad ediciones de orígenes diferentes.

## Resolución de países

Se parte de los **196 países GWNO congelados** del proyecto y se hace la correspondencia con el ISO3 del Banco Mundial mediante coincidencia exacta de denominaciones normalizadas o una lista de excepciones GWNO→ISO3 auditada. No hay fuzzy matching ni imputación de valores ausentes. Kosovo y las categorías territoriales históricas se manejan explícitamente; se excluyen de forma conservadora territorios sin representación equivalente.

Se conservan en el resultado los GWNO emparejados, los casos excluidos y los valores país-año usados, para auditar cualquier divergencia. Se exige una cobertura mínima de 155 países por año para producir comparaciones.

## Tres preguntas separadas

1. **Concordancia contemporánea, 2012–2025**: entre pares de países del mismo año, ¿tienen menor valor WGI aquellos cuyo UCDP registra ≥25 muertes? Se usa la AUC ordinal de comparación entre casos activos y no activos. AUC 0,5 = ausencia de ordenación; 1 = todos los activos con WGI menor.
2. **Contraste retrospectivo a dos años, orígenes 2012–2023**: ¿en qué grado el índice WGI del origen ordena por separado los países activos en UCDP dos años después? La edición WGI 2026 se ha reconstruido retrospectivamente, por lo que **no** puede afirmarse que los valores de esos años estuvieran publicados entonces. Se informará AUC histórica, nunca habilidad prospectiva.
3. **Contexto para la emisión 2027**: Spearman de la menor estabilidad percibida WGI2025 frente al riesgo de cuatro estados H2 de 2027 ya registrado. **No existen etiquetas de 2027**, ni se deducen de WGI2025. Solo es una comparación de ordenaciones, no una prueba de acierto.

## Fuentes alternativas estudiadas

- **ACLED** es más próximo al concepto de eventos violentos, pero acceder a su API requiere cuenta y autenticación. No se inventan credenciales ni se fusionan eventos que no se han obtenido.
- **Correlates of War** publica guerras bajo umbrales distintos y añade limitaciones de reutilización y redistribución; no resulta un sustituto directo del recuento UCDP ≥25.
- **V-Dem** ofrece medidas de democracia y violencia, pero su descarga oficial puede requerir aceptar condiciones y aportar datos; tampoco es una anotación de fallecidos idéntica a UCDP.

Fuentes metodológicas: [World Bank, WGI preguntas frecuentes](https://www.worldbank.org/en/publication/worldwide-governance-indicators/frequently-asked-questions), [World Bank Data API](https://datahelpdesk.worldbank.org/knowledgebase/articles/889392), [ACLED API](https://acleddata.com/api-documentation/getting-started), [COW Data Sets](https://correlatesofwar.org/data-sets/).

## Protocolo de aprobación

SHA de UCDP26.1, serie WGI oficial normalizada e identificada, cobertura por país-año explícita, ninguna imputación 0, pruebas de AUC y Spearman con dirección verificable, todas las 196 emisiones previas intactas y auditoría pública institucional. Las cifras se insertarán después de la ejecución inicial y antes de fusionar.

Informe futuro: `data/geo-h2-wgi-political-stability-contextual-concordance.json`.

## Resultados oficiales reproducidos

El emparejamiento exacto por GWNO/ISO3, con excepciones explícitas verificadas, ha cubierto **194 de los 196 países** de la cohorte. Solo permanecen excluidos los GWNO **327 (Ciudad del Vaticano)** y **713 (Taiwán)**, por falta de correspondencia institucional que pueda garantizarse bajo el protocolo. No se imputaron observaciones ausentes ni se usaron nombres aproximados.

Se ha almacenado el contenido numérico de la consulta oficial WGI de 2012–2025, con **2.885 observaciones disponibles en los territorios ISO3 consultados** y SHA-256 normalizada **`77959f040db841106c37d83de9cdeeca774b4575266efb3a1ae552facd6ff6e9`**. El análisis utiliza **194 países en cada uno de los 14 años**, todos con recuentos UCDP 26.1 y estimación WGI del mismo año.

| Año | AUC ordinal contextual: WGI menor en países con UCDP ≥25 muertes | Países emparejados |
|---|---:|---:|
| 2012 | 0,9636 | 194 |
| 2013 | 0,9439 | 194 |
| 2014 | 0,9636 | 194 |
| 2015 | 0,9711 | 194 |
| 2016 | 0,9545 | 194 |
| 2017 | 0,9590 | 194 |
| 2018 | 0,9537 | 194 |
| 2019 | 0,9499 | 194 |
| 2020 | 0,9704 | 194 |
| 2021 | 0,9608 | 194 |
| 2022 | 0,9513 | 194 |
| 2023 | 0,9586 | 194 |
| 2024 | 0,9624 | 194 |
| 2025 | 0,9507 | 194 |

En 2025, la estimación media de estabilidad percibida fue **−1,4142** para 34 países con al menos 25 fallecidos según UCDP y **+0,3100** en los otros 160 países. El contraste ordinal es alto, pero mide **concordancia de constructos parcialmente relacionados**, no precisión de recuentos ni verdad latente.

Para el diagnóstico retrospectivo con indicador de origen y violencia dos años después se reconstruyeron doce comparaciones 2012→2014 a 2023→2025, con AUC por año disponible en el informe. Estos valores no son validación prospectiva: WGI consultado actualmente incorpora revisiones y publicaciones posteriores a los años simulados.

En la comparación **WGI 2025 vs probabilidades H2 ya registradas para 2027** (sin observar los resultados de 2027), la correlación de rangos de Spearman entre mayor riesgo H2 y menor estabilidad WGI es **+0,7691** en los 194 países. Esto señala similitud entre ordenaciones, no que las probabilidades estén calibradas o que predigan correctamente 2027.

**Decisión científica:** la evidencia del Banco Mundial es consistente con la intensidad geopolítica de UCDP a nivel agregado, pero no identifica la categoría verdadera de fallecidos para Ruanda, Burundi, Venezuela ni otros casos específicos. Para verificar discrepancias de conteos se requiere evidencia independiente con eventos, fechas, localizaciones y criterios de muertes comparables; la mayor AUC contextual no resuelve esa necesidad.

[Informe JSON SHA con los 194 países, cobertura y 14 años](../data/geo-h2-wgi-political-stability-contextual-concordance.json) · [Reproductor oficial](../scripts/experiment_geo_h2_worldbank_wgi_external_context.py) · [Pruebas de mapeo y métricas](../scripts/test_experiment_geo_h2_worldbank_wgi_external_context.py).
