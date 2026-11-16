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

## Hallazgos oficiales: nueve, quince y doce países deciden el contraste

Las cuatro ediciones UCDP SHA-verificadas reproducen los **30 bloques año-edición** y la totalidad de los Brier del estudio cronológico precedente. En la última versión **UCDP 26.1**, las diferencias exactas α=1 menos α=0 para los tres años de interés son:

| Objetivo | Países con muertes 0 | Países con muertes 1–24 | Países con muertes ≥25 | Eventos objetivo ≥25 dentro de los 1–24 | Brier α1−α0 |
|---|---:|---:|---:|---:|---:|
| 2017 | 153 | **9** | 34 | 2 | **+0,000111463** (α0 favorecido) |
| 2024 | 144 | **15** | 37 | 2 | **−0,000787887** (α1 favorecido) |
| 2025 | 150 | **12** | 34 | 1 | **+0,000619652** (α0 favorecido) |

Las columnas son estados de *origen*, dos años antes del objetivo, y no conteos de conflictos futuros. Esas 9, 15 y 12 observaciones representan **4,6 %, 7,7 % y 6,1 %**, respectivamente, de los 196 casos del Brier anual. En los demás países, la diferencia de error entre las dos variantes es **exactamente cero**, aunque algunos sí experimenten violencia ≥25 en el objetivo.

### Descomposición exacta de ganancia y perjuicio

El efecto neto Brier procede del compromiso entre incrementar acertadamente la probabilidad de países que cruzan el umbral y generar probabilidades demasiado altas para países que no lo cruzan. La pérdida Brier se calcula **por país antes de dividir entre 196**:

| Año | Reducciones de pérdida α1 en países 1–24 que llegan a ≥25 | Aumentos de pérdida α1 en países 1–24 que no llegan a ≥25 | Total antes de dividir entre 196 |
|---|---:|---:|---:|
| **2017** | **−0,047639** (2 países) | **+0,069486** (7 países) | **+0,021847**, perjudica α1 |
| **2024** | **−0,456044** (2 países) | **+0,301618** (13 países) | **−0,154426**, beneficia α1 |
| **2025** | **−0,034403** (1 país) | **+0,155854** (11 países) | **+0,121452**, perjudica α1 |

Esta es la explicación estrictamente estadística de las inversiones. **La señal LOG1P no se comporta mejor o peor uniformemente por país**; el efecto agregado depende de si el aumento de probabilidad en los pocos países 1–24 que cruzan el umbral compensa el coste de los que permanecen inactivos.

### Países con más influencia en cada año

- **2017 · Israel:** 10 muertes en el origen y **resultado inactivo**. Pasar de α0 a α1 eleva la probabilidad reconstruida de **21,93 % a 31,26 %**, aumentando la pérdida Brier **+0,049619** (suma antes de dividir entre 196). La mejora combinada de los únicos dos países subumbral que se activan, **Angola y Bangladesh**, aporta **−0,047639**. **Si se quita Israel del promedio anual, manteniendo los coeficientes ajustados, cambia el signo** y α1 pasa a favorecerse. No se ha reentrenado el modelo al eliminarlo.
- **2024 · Angola y Sudán del Sur:** 20 y 23 muertes al origen y **resultado activo**. α1 mejora la pérdida Brier de Angola **−0,309445** (probabilidad **19,09 %→41,25 %**) y Sudán del Sur **−0,146599** (**4,30 %→12,29 %**), superando el perjuicio de 13 países que no se activan. El mayor perjuicio individual de este último grupo corresponde a **Burundi**, **+0,108717**. **Si se omite Angola del promedio, sin reentrenar, se invierte el signo de 2024**.
- **2025 · Uganda, Armenia y Arabia Saudí:** parten de 22, 20 y 9 muertes, respectivamente, y permanecen inactivos. Sus aportaciones de pérdida adicional son **+0,055902**, **+0,029634** y **+0,029473**. El único país con 1–24 muertes que cruza el umbral y mejora la pérdida gracias a α1 es **Sudán del Sur**, con dos muertes al origen (**−0,034403**). **Eliminar un solo país del cálculo no revierte la dirección anual**: el perjuicio está más repartido entre varias observaciones.

**No confundir estas contribuciones con probabilidades reales de estallido de conflicto ni atribuir causalidad por el mero incremento de muertes históricas.** El modelo predice un umbral contable anual definido por UCDP y los movimientos son comparaciones algebraicas de error.

### ¿Las revisiones entre ediciones alteran la explicación?

- Para **2017**, el mismo conjunto de **9 países** con muertes de origen entre 1 y 24 se mantiene en **las cuatro ediciones 23.1, 24.1, 25.1 y 26.1**. Ninguna contribución individual cambia de signo entre ediciones.
- Para **2024**, el conjunto de **15 países** se mantiene en **las dos ediciones 25.1 y 26.1** disponibles. Tampoco cambia el signo de ninguna contribución individual.
- Para **2025**, únicamente se dispone de la edición **26.1**, de modo que **no existe réplica editorial de ese año** para determinar si la atribución se mantendría tras una futura revisión.

En estos tres objetivos los signos del Brier global coinciden en todas las ediciones disponibles, pero **esto no prueba invariancia frente a revisiones aún no publicadas** ni convierte a las ediciones solapadas en ensayos estadísticos independientes.

### Consecuencia para el diseño del modelo

Se identifica una limitación estructural más relevante que una mera oscilación de Brier: aunque se evalúen **196 países**, la señal incremental para diferenciar α1 de α0 procede de solo **9–15 países por año** en los ejemplos auditados. Su peso en el resultado se amplifica cuando alguno llega a cruzar el umbral. Por ello, las mejoras en siete de nueve años retrospectivos **no bastan para demostrar estabilidad estructural o generalización**, especialmente cuando el modelo puede ser muy sensible a revisiones de los recuentos 1–24.

**Regla de investigación:** mantener congelados GEO original y sombra LOG1P de 2027; registrar por separado utilidad predictiva futura y sensibilidad de fuentes. No escoger ahora un coeficiente optimizado sobre 2017, 2024 o 2025 ni convertir el leave-one-out descriptivo en validación de generalización.

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
