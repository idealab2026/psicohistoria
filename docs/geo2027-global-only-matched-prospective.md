# GEO2027 — Emisión prospectiva independiente: Markov global-only con calibración LOG1P emparejada

## Contrato prospectivo registrado antes de los resultados de 2027

Se emite un **nuevo comparador prospectivo independiente**, destinado a evaluar todo el mismo universo de **196 identificadores GWNO** del GEO2027 original, para el resultado anual definido por UCDP OrganizedViolenceCY **state-based `sb_total_deaths_best >= 25` en 2027. El origen de pronóstico es **2025**, horizonte 2, edición fuente oficial **UCDP 26.1**, con ZIP SHA-256 `66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`. **Ningún resultado oficial de 2027 está disponible ni se utiliza**.

No se modifica la primera emisión GEO2027, la sombra LOG1P ya emitida ni las 15 alertas. Este nuevo experimento **no cambia su clasificación, sus probabilidades ni su ordenación**. Su archivo de 196 países, una vez publicado, queda inmutable; la primera versión completa se identifica por su SHA-256 y el primer commit público de GitHub, sin presentarlo como notarización independiente.

## Arquitectura y entrenamiento íntegramente consistente

Las investigaciones anteriores demostraron que el historial nacional influye en Markov y que un calibrador logístico aprendido sobre offsets Markov locales puede estar desajustado al utilizar offsets global-only. La investigación #99 corrigió ese desajuste retrospectivamente **solo para 143 casos de países subumbrales**. Esta nueva emisión cubre **los 196 países, activos e inactivos**.

Para **cada país objetivo \(c\)** de los 196 se entrena, usando las etiquetas oficiales históricas **2012–2025**, una regresión logística con offset H2 y regularización ridge λ=5 ya definida previamente. Se quitan del conjunto supervisado **todas las filas históricas de \(c\)**. Para cada otra fila de entrenamiento del país \(i\neq c\) y año objetivo \(u\le 2025\):

- El Markov global H2 de la fila usa datos únicamente hasta **\(u-2\)**, y excluye del agregado de transiciones tanto a **\(c\)** como a **\(i\)**. No se utilizan las transiciones locales de \(i\) en el score.
- El entrenamiento conoce el estado binario y las muertes de origen de **\(i\)** en \(u-2\), porque son variables observadas al momento de pronosticar \(u\).
- La regresión se ajusta a etiquetas de los otros países con esta **misma familia de offsets global-only**, en vez de emplear un calibrador local incompatible.

Para el pronóstico de **\(c\)** en 2027, el Markov se calcula sobre las transiciones históricas de todos los países **excepto \(c\)** hasta 2025; utiliza su estado binario de 2025 y el conteo de muertes de 2025 en la corrección LOG1P. La predicción de horizonte dos es \((1-g_{s_{2025}})g_0+g_{s_{2025}}g_1\), con prior global Laplace-1, sin shrinkage de transiciones propias. Se guarda el vector β específico aprendido sin el historial de \(c\).

Para cada país se publican **dos brazos ya definidos antes de los resultados** con el mismo vector β: **α=1**, pendiente continua subumbral completa; **α=0**, pendiente subumbral desactivada; intercepto y pendiente activa idénticos. El modelo no selecciona α por Brier histórico. Ambos brazos son iguales cuando las muertes de origen son 0 o ≥25.

## Contrato de puntuación futura sobre el universo completo

En cuanto exista la **primera edición oficial de UCDP que contenga etiquetas 2027 completas para los 196 países fijados**, se evaluará el mismo vector de resultados contra cinco probabilidades por país:

1. Original GEO 2027 **ya congelado**.
2. Sombra LOG1P del GEO original **ya congelada**.
3. Calibración solo-intercepto existente como control.
4. **Global-only matched α=1**, nueva emisión.
5. **Global-only matched α=0**, nuevo brazo de sensibilidad predefinido.

**Comparación principal registrada antes de 2027:** diferencia Brier emparejada sobre los **196 países**, \(\Delta=Brier(\text{global-only matched α=1})-Brier(\text{LOG1P original congelado})\). Negativa favorecería el nuevo candidato, positiva al modelo previo. **La comparación principal no implica que ya haya evidencia de superioridad.**

Comparaciones secundarias: α=0 frente a α=1 dentro del global-only, ambos global-only frente al GEO original, α=0 frente al LOG1P congelado y log-loss de los pares principales. Reportar **todos los resultados**, incluidas pérdidas y empates. No alterar los umbrales, seleccionar un año favorable, ajustar nuevos β o publicar versiones sustitutas después de observar 2027. Las ediciones UCDP posteriores a la primera completa se usarán **solo para sensibilidad a revisión de fuente**. Una etiqueta faltante o no validada **nunca se codifica como 0**.

**Precisión inferencial:** el número de países que superan el umbral es una variable común y geopolíticamente correlacionada; el score país-año permite una comparación descriptiva emparejada de 196 casos, **no una prueba de independencia ni p-valores binomiales IID**. Con al menos cinco brazos comparables, tampoco puede declararse confirmatorio al «mejor entre todos» tras observar el resultado. El contraste principal se registra antes del resultado, pero **la arquitectura y λ=5 se eligieron después de estudiar resultados históricos** (2017–2025), y no forman un holdout histórico nuevo. La única validación genuinamente prospectiva será la puntuación futura de 2027, aún no observada.

## Reproducibilidad e inmutabilidad

- El ZIP UCDP 26.1 se verifica contra el SHA oficial archivado por el laboratorio antes de calcular.
- Las 196 probabilidades originales GEO (`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`), las 196 LOG1P existentes (`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`) y las 15 alertas (`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`) se cotejan antes de cada generación.
- **196 ajustes diferenciados**, con exclusión de todas las filas históricas y transiciones propias; todos los historiales de entrenamiento llegan a lo sumo a etiquetas **2025** y sus variables a **2023**. La evaluación 2027 usa únicamente estado y muertes observadas en **2025**.
- El primer archivo completo es canónico, SHA-pinned y auditado por GitHub Actions. El manifiesto institucional registra el primer commit completo. La hora y SHA de GitHub son evidencia de publicación, **no notarización criptográfica independiente**.
- Las probabilidades nuevas nunca sustituyen los artefactos antiguos; no se emiten alertas adicionales y **0 resultados oficiales 2027 están resueltos**.

Código: `scripts/prepare_geo2027_global_only_matched_shadow.py`. Test de fugas y exclusiones: `scripts/test_prepare_geo2027_global_only_matched_shadow.py`. Emisión: `data/forecast-2027-global-only-matched-shadow.json`. Manifiesto: `data/forecast-2027-global-only-matched-manifest.json`. Auditoría inmutable: `scripts/audit_geo2027_global_only_matched_issue.py`.
