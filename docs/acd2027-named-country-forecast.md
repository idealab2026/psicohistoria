# ACD-2027 — Países y probabilidades del primer pronóstico emitido

La línea ACD emitió **antes de conocer el resultado de 2027** un conjunto de **32 países con conflicto intraestatal registrado en 2025**. El archivo original, sus tres probabilidades por país y su primer commit público son inmutables: `data/forecast-2027-acd-retention.json`, SHA-256 `6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c`, primer commit `41db7bd154e0140ced15abd8727a7d52d998852c`.

Este nuevo documento describe únicamente una **vista legible** derivada: la clave `gwno_a=gwno_loc` de cada país original ACD se cruza por igualdad numérica exacta con el campo `country_id` del compromiso GEO-2027 de **196 países** (SHA-256 `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`). Se han identificado los **32 códigos**, sin pérdida de nombres ni asignación aproximada.

El programa `scripts/publish_acd2027_named_country_view.py` construye `data/forecast-2027-acd-retention-country-view.json` con nombre original institucional, las tres probabilidades intactas, estado conocido de 2024 y número de casos históricos usados para cada país. Una clasificación secundaria ordena por la probabilidad de persistencia estimada con historia específica de cada país. **Esa clasificación no ha demostrado ser un mejor predictor que la referencia global**: la exploración de 2021–2024 mostró una mejora inestable del otro modelo de actividad previa. El modelo **primario fijado antes de la emisión** sigue siendo la tasa global reciente de 0,859195402299 aplicada a cada uno de los 32 países. Como es idéntica para todos, **no produce un ranking de países**.

## Lectura de la vista derivada

Ejemplos de las probabilidades **secundarias de historia de país**, ordenadas por el valor emitido:

| País | Probabilidad secundaria de persistencia ACD en 2027 |
|---|---:|
| Colombia | 94,72 % |
| Afganistán | 94,72 % |
| India | 94,72 % |
| Myanmar | 94,72 % |
| Filipinas | 94,72 % |
| … | … |
| Níger | 73,47 % |
| Ruanda | 71,43 % |
| Irán | 69,33 % |
| Haití | 68,36 % |

**No** se trata de la probabilidad de que estos países estén en guerra en el sentido coloquial, de que el conflicto aumente o disminuya, ni de un umbral de muertes en 2027. La variable es si UCDP/PRIO ACD registra **al menos un conflicto intraestatal tipo 3 o 4** en ese país durante el año 2027, **condicionada a que lo registró en 2025**. Una etiqueta negativa en 2027 tampoco implica paz o ausencia de otros tipos de violencia.

Las probabilidades son pronósticos genuinamente anteriores al resultado, pero la selección de modelo es exploratoria tras examinar datos históricos; ninguna ha sido validada en 2027. Tampoco es posible atribuir a una diferencia de probabilidad un grado probado de calibración individual. La puntuación principal sigue siendo el Brier sobre **los mismos 32 países** cuando se publique y certifique la primera edición UCDP/PRIO completa que cubra 2027.

La auditoría pública compara **byte a byte** la vista derivada con sus fuentes originales congeladas. Prohíbe cambios en probabilidades, países y primeras emisiones de GEO-2027, ACD-2027, shadow, alertas y NEWCONF-2027. No se han observado resultados de 2027.
