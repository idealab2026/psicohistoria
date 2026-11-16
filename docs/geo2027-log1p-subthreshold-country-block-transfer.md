# GEO2027 LOG1P — Transferencia de la señal subumbral entre países

**Protocolo retrospectivo · 16/11/2026.** Este experimento es continuación de la atribución Brier publicada para 2017, 2024 y 2025. No cambia ni reemite la predicción GEO2027, su sombra LOG1P o sus 15 alertas.

## Pregunta científica

El signo anual de la ventaja de la intensidad continua se decide por apenas 9–15 países que parten de **1–24 muertes estatales UCDP en el origen**, dentro de 196 países evaluados. Los estudios precedentes retiraban un país del *cálculo de Brier* sin reajustar los parámetros, lo cual no comprueba si la señal se transmite a otro país mediante un calibrador entrenado sin sus observaciones.

Este estudio lleva a cabo un **reajuste real de los coeficientes logísticos por país omitido**, manteniendo el componente GEO Markov original.

## Protocolo

Para cada año retrospectivo de resultado \(t\), el origen del forecast H2 es \(t-2\). La logística con regularización ridge **λ=5**, fijada previamente, utiliza solo años de etiqueta \(u=2012,\ldots,t-2\), y todos sus predictores históricos se construyen con información hasta \(u-2\leq t-4\).

Por cada país con \(1\leq d_{t-2}\leq24\):

1. Retirar **todas las filas supervisadas históricas del país** antes de ajustar los coeficientes; no basta con excluir su última observación.
2. Ajustar los tres coeficientes originales LOG1P a los demás países, manteniendo penalización ridge 5 y mismas funciones de intensidad.
3. Aplicar esos coeficientes al país excluido, usando su **probabilidad GEO H2 original calculada al año de origen** y sus muertes estatales del origen. La etiqueta del año objetivo solo aparece en la evaluación.
4. Contrastar α=0 y α=1, con las mismas definiciones preestablecidas: α multiplica únicamente la pendiente de los países con menos de 25 muertes en el origen.
5. Publicar Brier diferencial del subconjunto 1–24, la contribución normalizada respecto a los 196 países, diferencias respecto al calibrador completo, desplazamiento de coeficientes y resultados según activación real posterior.

**Distinción esencial:** el Markov original *conserva la historia anterior del país evaluado* (transiciones nacionales y peso en el prior global) porque el objetivo es predecir un país conocido. Esto evalúa **transferencia internacional de la calibración LOG1P**, no un país completamente nuevo (*cold start*) ni un Markov reentrenado sin ese país. Los ajustes se obtienen solo de otros países, pero el offset Markov sí dispone de historia propia.

## Ámbito temporal

Se comprueban **nueve años distintos, 2017–2025, de la edición oficial UCDP 26.1**; adicionalmente 2017 se repite con 23.1, 24.1 y 25.1, y 2024 con 25.1. Son **13 bloques año–edición**, con países y años solapados, no 13 réplicas independientes. Para 2017, 2024 y 2025 se conserva cada contribución individual. Las cuatro fuentes se verifican mediante SHA-256 antes de la reproducción.

El coeficiente λ=5, la familia LOG1P y los años seleccionados **fueron definidos en 2026 después de inspeccionar parte del histórico**. Los contrastes son exploratorios incluso si la formación del coeficiente respeta la cronología interna; tampoco reconstruyen fielmente las versiones UCDP disponibles en cada fecha histórica. No se escoge un nuevo modelo ganador ni se reclama rendimiento prospectivo o significación estadística IID.

## Seguridad y reproducibilidad

Auditoría obligatoria de los tres archivos originales de 2027: GEO original (SHA-256 5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5), sombra LOG1P (SHA-256 52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90) y 15 alertas (SHA-256 309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb).

Las pruebas verifican que no entra ninguna etiqueta posterior al origen, que **cada fila histórica del país es excluida del calibrador** y que el ajuste completo coincide con el informe anual publicado. La acción de GitHub recupera las cuatro ediciones oficiales, recalcula el documento y compara su contenido byte a byte. No existen etiquetas oficiales resueltas para 2027.

Archivos: scripts/experiment_geo2027_log1p_country_block_transfer.py; scripts/test_experiment_geo2027_log1p_country_block_transfer.py; data/geo2027-log1p-subthreshold-country-block-transfer.json.
