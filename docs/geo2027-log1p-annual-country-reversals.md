# GEO2027 · ¿Qué países explican las inversiones anuales de Brier de LOG1P?

**Protocolo de investigación retrospectiva, 16 de noviembre de 2026.** Las series H2 reproducidas en las cuatro ediciones oficiales UCDP muestran que la pendiente continua de muertes mejora el Brier en 2018–2024, pero lo empeora en 2017 y 2025. Este estudio identifica **qué observaciones país-año** generan ese cambio, sin formular explicaciones causales de los conflictos.

## La identidad matemática que permite una atribución exacta

Se comparan exclusivamente dos variantes ya estudiadas:

- **α=0:** la intensidad adicional de muertes en el origen se anula solo para países inactivos, con muertes best inferiores a 25.
- **α=1:** la intensidad continua LOG1P se conserva íntegramente.

Ambas utilizan idéntico Markov H2, intercepto, coeficiente para países activos y entrenamiento de coeficientes. Cada año objetivo histórico \(t\) se evalúa con un ajuste creado **solo con etiquetas hasta \(t-2\)**; las variables de las observaciones de entrenamiento alcanzan como máximo \(t-4\). No se consulta ningún resultado \(t-1\) ni \(t\) para ajustar el modelo de ese año.

La diferencia individual de pérdida cuadrática queda completamente determinada por:
\[
\Delta_i=(p_{\alpha=1,i}-y_i)^2-(p_{\alpha=0,i}-y_i)^2
=(p_{\alpha=1,i}-p_{\alpha=0,i})(p_{\alpha=1,i}+p_{\alpha=0,i}-2y_i).
\]

Para \(n\) países con origen/resultado observados, la diferencia Brier anual es exactamente \(\frac1n\sum_i\Delta_i\).

**Hecho estructural:** si las muertes de origen son **0**, la variable continua inactiva es cero y **\(p_{\alpha=1}=p_{\alpha=0}\)**. Si son **≥25**, ambos modelos tienen el mismo coeficiente de intensidad activa; de nuevo, **las probabilidades son idénticas**. Por tanto, **solo los países con entre 1 y 24 muertes estatales best en el origen pueden explicar el signo de la comparación α=1 vs α=0**. Aunque la media se calcule sobre la cohorte de referencia, todos los demás países aportan exactamente \(\Delta_i=0\). No basta con mirar el tamaño global de la muestra (196) para juzgar la estabilidad de esa comparación.

## Descomposición publicada y controles de interpretación

Se reconstruyen **30 bloques año-edición** procedentes de los cuatro archivos UCDP 23.1–26.1 (objetivos 2017–2025, nueve años distintos) y se exige que su Brier anual, signo de diferencia y coeficientes coincidan con el informe ya publicado \`geo2027-log1p-rolling-year-vintage-stability.json\`.

Para cada año y versión se publican por separado:

1. Número de países con muertes de origen **0**, **1–24**, **≥25**, con etiquetas directamente observadas.
2. Número y suma de contribuciones Brier de países sin activación futura y países que pasan de inactivos a activos, además de los dos grupos que parten activos. \(\Delta_i\) **negativa** significa que mantener la señal continua reduce Brier; **positiva** significa que lo aumenta.
3. Contribuciones positivas perjudiciales y negativas beneficiosas, la fracción de influencia absoluta concentrada en los principales países, y la comprobación de que su suma reproduce exactamente el Brier anual.
4. **Influencia de omitir un país del cálculo de la métrica, manteniendo el modelo ya ajustado**. Si el signo cambia, queda documentada la sensibilidad del promedio a esa observación. Esto **no** es una validación leave-one-country-out que reajuste \(\beta\), ni un experimento causal.
5. Listado detallado de todos los países de origen 1–24 para **2017, 2024 (comparador) y 2025**, y cambios en la identidad, intensidad, outcome y contribución entre las ediciones oficiales que contienen el mismo año. El año 2025 solo aparece en 26.1 y **no tiene otra edición con que contrastar**.

No se atribuye una discrepancia individual a un acontecimiento histórico concreto sin corroboración independiente. La notación «ganancia de precisión», si apareciese, significa estrictamente *disminución de la puntuación Brier en la reconstrucción*, no conocimiento causal de un suceso. No se selecciona un nuevo modelo con los años retrospectivos y no se considera que 30 bloques solapados constituyan 30 observaciones independientes.

**Control de privacidad y emisiones:** datos públicos exclusivamente de IDEA LAB. Permanecen byte idénticos el GEO2027 original, su sombra prospectiva LOG1P y las 15 alertas, anclados por sus SHA. **Cero resultados oficiales de 2027 puntuados**; no se emiten nuevas probabilidades ni alertas.

**Reproducción:** \`scripts/diagnose_geo2027_log1p_annual_country_reversals.py\`, pruebas \`scripts/test_diagnose_geo2027_log1p_annual_country_reversals.py\`, informe \`data/geo2027-log1p-country-year-reversal-attribution.json\`. GitHub Actions reconstruye el informe desde las cuatro fuentes UCDP verificadas por SHA y bloquea la publicación si no coincide byte a byte.
