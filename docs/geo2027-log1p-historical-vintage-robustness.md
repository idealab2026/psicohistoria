# GEO2027 LOG1P · Sensibilidad a revisiones históricas de UCDP (fuentes 23.1–26.1)

**Investigación retrospectiva · 16/11/2026.** El experimento estudia **la estabilidad de la familia de modelos LOG1P** cuando una edición oficial de UCDP modifica muertes históricas. **No cambia, reemite, reentrena ni invalida automáticamente las 196 probabilidades de la sombra prospectiva emitida el 16/11/2026**.

## Restricción científica: el origen de 2025 no puede simularse usando ediciones anteriores

La sombra real de 2027 tiene **origen en 2025** y utiliza UCDP 26.1. Las ediciones 23.1, 24.1 y 25.1 terminan en 2022, 2023 y 2024; por tanto **no contienen datos de 2025**. Sería falso reconstruir en ellas «lo que habría predicho» exactamente la sombra 2025→2027.

Se compara la **misma arquitectura** en cohortes retrospectivas históricamente análogas, con los mismos 196 identificadores GWNO y dos fechas de origen fijadas, siempre quitando datos posteriores al origen antes de cualquier entrenamiento:

| Origen retrospectivo | Edición inicial | Ediciones oficiales revisadas | Horizonte |
|---|---|---|---|
| 2022 | 23.1 | 24.1, 25.1, 26.1 | H2 → 2024, solo **simulado** |
| 2023 | 24.1 | 25.1, 26.1 | H2 → 2025, solo **simulado** |

Son cinco **pares correlacionados, no cinco experimentos independientes**. Tampoco son evaluaciones de resultado: aquí **no se consultan las etiquetas 2024/2025 como resultados a puntuar**. Para cada edición se ajustan el Markov GEO H2 y la regresión LOG1P desde cero con los mismos procedimientos ya congelados, incluyendo selección de penalización **5,20,80** con etiquetas internas 2018–2020 y entrenamiento final solo hasta el origen de 2022 o 2023. Las probas H2 de la edición original deben reproducir los coeficientes publicados en el estudio precedente.

## Separar tres causas de revisión sin doble contabilización

La sombra histórica LOG1P se escribe como

\[
p_{\mathrm{LOG1P}}=f(p_{\mathrm{GEO}},d_{\mathrm{origen}},\boldsymbol\beta)
=\sigma\left[\operatorname{logit}(p_{\mathrm{GEO}})
 +\beta_0+\beta_Ix_I(d)+\beta_Ax_A(d)\right].
\]

Se reconstruyen tres factores, en cada una de sus dos versiones oficiales:

- **\(p_{\mathrm{GEO}}\)**: revisión de toda la historia binaria y de las tasas globales y locales de transición de Markov.
- **\(d_{\mathrm{origen}}\)**: cambio del número de muertes best en el año fijo de origen, sin reentrenar ni sustituir los otros factores.
- **\(\boldsymbol\beta\)**: cambio en los coeficientes que se aprenden al ajustar la logística LOG1P sobre los datos históricos revisados, incluida su selección de lambda sin información posterior al origen.

Para atribuir la diferencia total \(f(P_1,D_1,B_1)-f(P_0,D_0,B_0)\) se calculan las **seis posibles órdenes de sustitución de los tres factores** y se promedian sus contribuciones; la **suma Shapley reproduce exactamente la variación total** sin residuo matemático. Las combinaciones mixtas de versiones son **contrafactuales aritméticos**, no ediciones reales UCDP ni mecanismos causales independientes. Los cambios en el histórico del país pueden afectar simultáneamente a Markov y a los coeficientes; la separación depende de la parametrización.

El protocolo obliga a distinguir cualquier país cuyo **estado binario del origen** cambie al revisar la edición. Esta clase se aísla en vez de confundir una reclasificación 0↔1 con una simple perturbación dentro de un estado. Los listados históricos top-10 de entrada y top-5 de salida se comparan en **grupos de riesgo de origen fijos**, registrando empates del límite sin declarar «entradas seguras» que dependan arbitrariamente de ellos. Son **listas retrospectivas análogas**, nunca las 15 alertas prospectivas originalmente emitidas.

## Métricas y controles

Por cada pareja de ediciones y cohorte fija se reportarán: media, mediana, P95 y máximo del desplazamiento absoluto de \(p_{\mathrm{LOG1P}}\) en puntos porcentuales; contraste de esos valores con el Markov original; número de cambios ≥2,5pp y ≥5pp; muertes revisadas en el origen, coeficientes y lambda antiguos/nuevos; aportaciones Shapley firmadas y absolutas; y swaps top-10/top-5 con identificación de empates.

Para que el estudio sea reproducible, **los cuatro ficheros UCDP se recuperan y validan con su SHA-256 oficial previamente registrado**. También se verifican byte a byte los documentos prospectivos ya emitidos: GEO original SHA-256 \`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5\`, sombra LOG1P SHA-256 \`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90\` y las 15 alertas SHA-256 \`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb\`.

**Conclusión admisible:** sensibilidad histórica del mecanismo bajo revisiones de fuentes archivadas. **Conclusiones no admisibles:** «hay X% de error de la predicción 2027», «se ha revisado la nueva sombra 2027», «el rendimiento futuro del modelo está validado», o «las cinco comparaciones son independientes». La primera evaluación prospectiva continúa pendiente de la primera edición UCDP completa de 2027, con los mismos 196 países.

**Implementación:** \`scripts/diagnose_geo2027_log1p_historical_vintage_robustness.py\`, pruebas \`scripts/test_diagnose_geo2027_log1p_historical_vintage_robustness.py\`, y el informe SHA-pinned \`data/geo2027-log1p-historical-vintage-robustness.json\`. La auditoría GitHub Actions debe reconstruir el reporte con bytes idénticos y bloquear el despliegue si difiere.
