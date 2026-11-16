# GEO2027 — Sombra prospectiva de intensidad continua LOG1P v1

**Protocolo de emisión, 16 de noviembre de 2026.** Variante adicional **separada** del pronóstico GEO2027 emitido el 10/11/2026, de la cohorte original de 15 alertas de transición y de la sombra de calibración anteriormente emitida. Nada se sustituye. Los resultados oficiales de 2027 todavía no están disponibles.

## Primera emisión efectiva registrada en GitHub

- **Primer commit público del archivo completo de 196 probabilidades:** [`a2af84346bd223d2a105cf727b3462cd0955fdac`](https://github.com/idealab2026/psicohistoria/commit/a2af84346bd223d2a105cf727b3462cd0955fdac), fechado por GitHub el **16/11/2026 a las 11:34:38 UTC**. Esta marca temporal es metadato público de GitHub, **no una notarización criptográfica independiente**.
- **SHA-256 íntegro del archivo canónico:** `52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`. Está fijado en el manifiesto y como constante de auditoría independiente; la reproducción desde el ZIP UCDP oficial debe coincidir **byte a byte**.
- **196 países originales**, mismos estados de origen 2025, mismo objetivo binario 2027. El archivo incluye, por país, probabilidad GEO original, control intercepto y sombra LOG1P, además de muertes oficiales 2025.
- **Modelo final:** ridge λ=**5**, seleccionado por validación interna 2018–2020, refit en **2.742 observaciones país-año** con objetivos 2012–2025. Coeficientes `[β₀, β_inactivo, β_activo] = [-0,337793886776; 1,185261838805; 1,934189190903]`. No se utilizaron resultados oficiales 2026/2027.
- **Suma de probabilidades para 2027:** GEO original **33,6254** países activos esperados, control intercepto **34,8377**, sombra LOG1P **35,9840**. Son sumas de probabilidades, **no** una observación de 36 países, una predicción del número exacto, ni un intervalo de riesgo agregado.

Ninguna de esas 196 probabilidades se modificará ante nuevas cifras históricas o una evaluación posterior; cualquier revisión exige nuevo identificador y nuevo registro. La fórmula fue seleccionada tras haber visto retrospectivamente 2024/2025, pero los **resultados oficiales de 2027 seguían sin conocerse al emitir** este archivo.

## Qué se fija, y qué significa «prospectivo»

Este estudio tiene **dos niveles de evidencia distintos**:

- La selección del enfoque \`log1p\` **se hizo después de examinar** resultados retrospectivos de 2024 y 2025. Por tanto, ni el mejor Brier histórico ni la comparación con la variante de cuatro estados constituyen una prueba confirmatoria independiente.
- La evaluación real de **2027 sí puede ser prospectiva**, siempre que **esta variante y sus 196 probabilidades se publiquen primero y permanezcan inmutables hasta conocerse la primera edición completa oficial UCDP con observaciones de 2027**. El documento de emisión y el commit público son la evidencia temporal; ni una fecha escrita ni un manifest autodeclarado acreditan por sí solos el momento de publicación.

El archivo canónico tendrá identificador **PSICO-GEO2027-STATEBASED25-LOG1P-INTENSITY-SHADOW-V1** y 196 países según los códigos Gleditsch–Ward originales. Solo se emite la probabilidad de superar **25 muertes anuales de violencia organizada estatal**, no un pronóstico de inicio de guerras, violencia contra civiles, elecciones o conflictos geográficos.

## Fórmula y entrenamientos completamente separados de 2027

La referencia inmutable es la emisión GEO2027 original, SHA-256 \`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5\` (origen 2025; UCDP OrganizedViolenceCY 26.1, SHA-256 \`66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34\`). Las 196 probabilidades originales y estados 2025 se reconstruyen de los bytes oficiales y se comprueban país por país.

Se aplica la transformación original del estudio de intensidad continua:

\[
\operatorname{logit}p_{\mathrm{shadow}} =
\operatorname{logit}p_{\mathrm{GEO}}
+\beta_0+\beta_I 1(d_{2025}<25)\frac{\log(1+d_{2025})}{\log(26)}
+\beta_A 1(d_{2025}\geq25)\frac{\log(1+d_{2025})-\log(26)}{\log(101)}.
\]

Se entrenan los coeficientes con observaciones de países-año históricas **2012–2025 del mismo original UCDP 26.1**. Cada observación de entrenamiento para el año objetivo \(t\) utiliza **exclusivamente un modelo GEO reconstruido con corte \(t-2\)** y las muertes nacionales de ese mismo año de origen. El umbral de resultados para ajustar los coeficientes es ≥25 muertes en \(t\). Nunca entra ningún año 2026 o 2027.

La penalización ridge se escoge entre **5, 20, 80** por validación interna 2018–2020, tras entrenar cada candidato en objetivos 2012–2017; después se reentrena con objetivos 2012–2025. Se congela también un **control solo-intercepto** con la misma penalización, para poder comparar tres modelos en 2027: original GEO, calibración de intercepto y alternativa continua.

**No se optimizan** hiperparámetros de la alternativa utilizando futuros resultados de 2027. Tampoco se vuelven a emitir las 15 alertas originales ni se declaran nuevos top-10/top-5: aunque la transformación afecte a las ordenaciones, este experimento evalúa **probabilidades sobre los mismos 196 países**.

## Contrato de evaluación 2027 preespecificado

1. Resultado por país: \`UCDP OrganizedViolenceCY country-year sb_total_deaths_best >=25\` en 2027, primera **edición oficial completa** para ese año.
2. Evaluación principal solo cuando los **196 países** tengan etiqueta inequívoca. Los países ausentes quedan **sin resolver** y no se suponen eventos negativos; ninguna puntuación parcial puede sustituir al contrato global.
3. Primaria: **diferencia de Brier pareada** entre nueva sombra y GEO original, mismos 196 países, \`Brier_shadow−Brier_original\`. Un valor negativo favorecería a la sombra. Secundarias: diferencia de log-loss e incremental frente al control de intercepto.
4. Publicar resultados **sin ocultar errores individuales**, con diagnósticos por estado de origen y cambios de fuente posteriores como análisis de sensibilidad, no como sustitutos de la primera edición oficial.
5. Tener en cuenta la **multiplicidad de variantes sombra** ya exploradas y la dependencia entre países; no presentar un test IID por país como si las 196 observaciones fueran independientes ni atribuir causalidad.
6. Nunca modificar la emisión, la primera fecha de publicación, las probabilidades ni las puntuaciones por conocer un resultado posterior. Si cambia el código/modelo en el futuro, se exige **nuevo identificador**, nueva emisión y evaluación distinta.

La publicación debe incluir un **SHA-256 del archivo prospectivo** en un manifiesto independiente con primera aparición visible en GitHub, y pruebas de reproducción a partir de la edición UCDP 26.1 con bytes verificados. La fecha escrita aquí corresponde a la preparación; **la fecha de emisión efectiva es la del primer commit que incluye todas las probabilidades**, no la fecha de este documento.

**Archivos:** \`scripts/prepare_geo2027_log1p_shadow.py\`, \`scripts/test_prepare_geo2027_log1p_shadow.py\`, \`data/forecast-2027-log1p-shadow.json\`, \`data/forecast-2027-log1p-shadow-manifest.json\`. Ninguno modifica la emisión original ni su histórico.
