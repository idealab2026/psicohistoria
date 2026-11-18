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
