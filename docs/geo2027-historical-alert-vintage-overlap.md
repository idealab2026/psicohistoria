# GEO2027 · Estabilidad histórica real de listas de alertas ante revisiones UCDP

**Tipo de estudio:** comparación retrospectiva de listas simuladas, no revisión de alertas publicadas.

## Pregunta y limitación de identificabilidad

El estudio de sensibilidad adversarial de las 15 alertas reales GEO2027 ([PR #84](https://github.com/idealab2026/psicohistoria/pull/84)) prueba qué puestos están garantizados al permitir cambios hipotéticos de probabilidad. Este estudio adicional pregunta qué ocurre al **reajustar el mismo modelo con ediciones históricas oficiales distintas**, manteniendo el mismo año de origen, el horizonte H2, la población inicial y los presupuestos de alertas (top-10 inactivos, top-5 activos).

**No es posible atribuir a una revisión real de la emisión 2027 el efecto entre UCDP 25.1 y 26.1:** UCDP 25.1 termina en 2024 y no contiene el estado de origen 2025 usado en esa emisión. No existe en las cuatro ediciones comparadas otra edición con información completa a 2025. Mezclar retrospectivamente 2025 desde 26.1 con una serie anterior produciría un panel híbrido **no publicado originalmente**, que no se presentará como revisión genuina.

Por tanto, realizamos **análogos retrospectivos sobre seis comparaciones reales de fuentes**: 23.1→24.1, 23.1→25.1 y 23.1→26.1 con origen 2022; 24.1→25.1 y 24.1→26.1 con origen 2023; 25.1→26.1 con origen 2024. En cada caso la fuente más reciente se recorta a **exactamente el mismo origen**, sin utilizar información de los años posteriores aunque exista en la edición revisada.

## Modelo, identificadores y pruebas

- UCDP OrganizedViolenceCY, variable binaria `sb_total_deaths_best >= 25` por país-año y GWNO. Las cuatro fuentes y sus SHA-256 están fijados en `scripts/backtest_archived_country_vintages.py`.
- Modelo Markov por país con suavizado global Laplace=1 y shrinkage=20; composición exacta de **dos pasos** como GEO2027. El motor reutiliza `_fit_at_origin` del estudio GEO2028 H2/H3 y el cálculo `nstep`.
- Se comparan **las mismas 196 identidades por pareja**. La pertenencia al grupo inactivo/activo se congela en el estado de origen de la **primera edición**; los cambios de estado de origen en la segunda edición se contabilizan aparte, evitando confundir composición del conjunto de riesgo con reajuste de probabilidades. Cuando no hay reclasificaciones, esta comparación es también la comparación entre ediciones completas en ese año.
- Ordenación por puntuación de transición descendente y desempate determinista **GWNO numérico ascendente**, igual al protocolo de las alertas publicadas.
- Cada pareja reporta el solapamiento exacto top-k, países que entran/salen y **dos tipos de cambios**: intercambios sujetos al desempate numérico y **entradas/salidas definitivas que sobreviven a cualquier desempate en la frontera**.
- En el caso de empates en la frontera, la pertenencia a una única lista no es un hallazgo estadístico. Se publican los conjuntos `mandatory` (están en cualquier top-k admisible) y `possible` (podrían entrar con algún desempate), de los que se derivan entradas/salidas definitivamente nuevas.
- Las seis parejas comparten observaciones, años e historial: **no son seis ensayos independientes**. El informe no estima intervalos de confianza, tasas de éxito, riesgo de guerra ni resultados de 2027.

## Integridad

La generación comprueba en cada ejecución las fuentes oficiales por sus hashes ya auditados, la primera emisión GEO2027 (`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`) y las 15 alertas originales (`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`). El reporte `data/geo2027-historical-alert-vintage-overlap.json` es **solo investigación** y no altera ni vuelve a emitir las 15 alertas reales.

Ejecución: `python3 scripts/diagnose_geo2027_historical_alert_vintage_overlap.py --check-report`.

La supervisión de publicación debe impedir cambios no autorizados y requerir una reconstrucción byte-a-byte del informe numérico desde las fuentes originales. **Cero resultados prospectivos 2027 resueltos**; ninguna habilidad predictiva futura demostrada.
