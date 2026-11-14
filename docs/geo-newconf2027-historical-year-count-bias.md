# GEO2027 + NEWCONF2027 · Descomposición histórica de errores anuales de recuento

**Estudio institucional · 14 de noviembre de 2026.** Análisis de fuentes UCDP históricas autenticadas por SHA-256. No usa datos de 2027, no cambia modelos ni emisiones originales y **no estima directamente correlación estructural entre países**.

## 1. Pregunta y diseño

Los estudios prospectivos de 2027 han demostrado matemáticamente que los shocks compartidos pueden incrementar la incertidumbre de las comparaciones entre modelos. Pero eso no demuestra que tales shocks estén presentes o que expliquen las desviaciones históricas observadas.

Para dar un paso empírico, examinamos los **recuentos de países con resultados registrados en cada año objetivo histórico**, comparándolos con las sumas de probabilidades de modelos ajustados exclusivamente con datos de sus años de origen. Por separado:

| Serie | Años objetivo retrospectivos | Ediciones oficiales y calidad temporal | Unidad |
|---|---|---|---|
| GEO, entradas 0→1 y resoluciones 1→0 | 2012–2023 | 26.1 revisada, mismo origen retrospectivo para ambas variables | Cambio del indicador de violencia estatal ≥25 muertes, origen t−2 |
| GEO, entradas y resoluciones | 2024 y 2025 | Origen 23.1→objetivo 25.1, y origen 24.1→objetivo 26.1 | Igual, pero fuentes separadas |
| NEWCONF, modelo de actividad vs global reciente | **2016–2022** | Fuente 23.1 Multiple Onset, retrospectiva/revisada; 7 orígenes 2014–2020, horizonte fijo de 2 años | País con ANY(newconf=1), **no** onset2 |
| NEWCONF, mismo modelo y horizonte | **2024** | Origen y variables de UCDP Multiple Onset 23.1 y ACD 23.1; etiquetas 2024 de Multiple Onset **25.1**, sin usarlas en entrenamiento | País-año ANY(newconf=1), 196 países |

**No mezclamos NEWCONF 2023 con las pruebas de horizonte dos años:** su experimento previo partía del origen 2022 y tenía horizonte de un año, por lo que añadirlo contaminaría la comparación.

En NEWCONF hay **1.372 evaluaciones país-año y 18 positivos** en los siete años revisados y **196 evaluaciones y un positivo** en la comprobación de 2024. Se agrupan los múltiples episodios de conflicto del mismo país-año en un único resultado binario. Los países se repiten; 1.372 no significa 1.372 repeticiones independientes del mismo fenómeno.

Los modelos históricos NEWCONF se han reconstruido desde la misma fórmula de desarrollo exploratorio original, no se han emitido realmente en sus orígenes. La pertenencia y la incidencia por país provienen solo de UCDP 23.1, no de la edición objetivo. La fuente 23.1 ya contenía información revisada respecto de orígenes 2014–2020: el bloque es **ex post**, no un ensayo ciego ni un as-of correctamente archivado.

## 2. Qué se puede descomponer exactamente

Para cada año objetivo t, se registra el número observado de países con evento K_t, el esperado E_t = suma de probabilidades individuales p_it y la varianza bajo **hipótesis de independencia** V_t = suma de p_it(1−p_it).

Definimos el residual anual normalizado:

\[
Z_t = \frac{K_t-E_t}{\sqrt{V_t}}.
\]

Dada una serie de T años, la identidad descriptiva exacta es:

\[
\frac1T\sum_t Z_t^2 =
\left(\frac1T\sum_t Z_t\right)^2 +
\frac1T\sum_t (Z_t-\overline Z)^2.
\]

El primer sumando es el **cuadrado del error medio firmado**, interpretable como componente de **sesgo direccional de recuentos**. El segundo es la variación temporal centrada que permanece. Esta identidad no es un modelo probabilístico causal, no infiere una correlación común y no prueba que la varianza restante se deba a dependencia entre países.

Las magnitudes se computan por año y modelo. Los horizontes y endpoints no se agregan para fabricar mayor tamaño muestral o un Brier común.

## 3. Resultados sobre los años revisados

| Serie | Años | Media de Z² | Media de Z | Sesgo medio² / media Z² |
|---|---:|---:|---:|---:|
| GEO entradas | 12 | **1,3565** | −0,8050 | **47,8 %** |
| GEO resoluciones | 12 | **3,0255** | −1,5742 | **81,9 %** |
| NEWCONF actividad-país | 7 | **2,8785** | +0,0938 | **0,3 %** |
| NEWCONF global-últimos-cinco años | 7 | **3,1864** | −0,8407 | **22,2 %** |

**Hallazgo GEO:** los dos modelos de recuento de cambios GEO sobreestiman históricamente, especialmente las resoluciones. El 81,9 % del error cuadrático normalizado medio de las resoluciones se descompone algebraicamente en sesgo medio. Interpretar el valor 3,03 como «dependencia entre conflictos» sería injustificable; un error marginal sistemático puede elevarlo sin correlación entre países.

**Hallazgo NEWCONF:** el modelo de actividad-país tiene media residual casi nula sobre 2016–2022, pero una gran variabilidad entre años: **2,87** de los **2,88** puntos de media Z² pertenecen al componente centrado. Esto es un patrón histórico descriptivo, **no un estimador de shocks comunes**: un modelo con tasas desactualizadas o heterogeneidad omitida, selección retrospectiva, desviaciones de fuentes o simple azar también puede producirlo.

Los recuentos NEWCONF de cada año histórico por el modelo de actividad-país son:

| Año | Países observados con newconf | Países esperados |
|---|---:|---:|
| 2016 | 6 | 1,59 |
| 2017 | 3 | 2,60 |
| 2018 | 1 | 2,93 |
| 2019 | 5 | 2,84 |
| 2020 | 1 | 2,72 |
| 2021 | 0 | 2,89 |
| 2022 | 2 | 2,80 |
| **2024, edición objetivo separada** | **1** | **2,57** |

El resultado de 2016 (6 observados frente a 1,59 esperados) concentra una fluctuación importante. No se han hecho inferencias de significación con un panel tan pequeño. La comprobación de 2024 procede de una edición posterior a la de origen, pero solo aporta **un año objetivo**.

## 4. Ensayo de estabilidad temporal del sesgo (diagnóstico, NO propuesta de recalibración)

Se calcula para cada nuevo año revisado t el residual Z_t menos la media de Z de los **años objetivo anteriores dentro de esta reconstrucción**: al menos 3 años previos para NEWCONF (se evalúan 2019–2022), y 4 para GEO (se evalúan 2016–2023). El ajuste no utiliza el resultado del año que se está evaluando, pero los archivos históricos fueron revisados con posterioridad y las fórmulas se analizan ex post.

| Serie | Media Z² sin ajuste en esos años | Media del cuadrado de (Z − media previa) |
|---|---:|---:|
| GEO entradas, 2016–2023 | 1,3144 | **0,6799** |
| GEO resoluciones, 2016–2023 | 3,0119 | **0,5637** |
| NEWCONF actividad-país, 2019–2022 | **1,5377** | **2,5696** |
| NEWCONF global-reciente, 2019–2022 | 2,7399 | **1,8465** |

**Advertencia decisiva:** la corrección descriptiva del sesgo ayuda en varios casos GEO, pero **perjudica al modelo NEWCONF de actividad-país** en los años elegidos. Esto demuestra por qué no conviene extrapolar mecánicamente una corrección de recuentos aprendida de pocos años. Además, corregir Z como agregado no define necesariamente probabilidades por país válidas, ni convierte el resultado en un backtest operativo prospectivo.

## 5. Comprobaciones por ediciones de origen y objetivo separadas

- **GEO2024 y GEO2025:** para las entradas, Z fue −1,1000 y −1,1139; en resoluciones, −1,1067 y −1,5599. El signo direccional de sobreestimación se mantiene en esas dos ediciones, pero la muestra es minúscula y comparte países con otras pruebas históricas.
- **NEWCONF2024:** 1 país positivo frente a **2,5719** esperados por actividad-país y **1,9959** por global-reciente. El residual Z de actividad-país es **−1,0006**. Una etiqueta agregada de 2024, aunque tenga fuente independiente, **no estima una covarianza país-país**.

No hay evidencia suficiente para decidir con estos datos si una determinada estructura de dependencia (independiente, bloque regional, shock global o anticorrelación de indicadores) se ajusta al comportamiento del mundo real. Los límites matemáticos de los estudios prospectivos anteriores permanecen como **escenarios de sensibilidad**, no probabilidades empíricamente estimadas.

## 6. Integridad y siguiente prueba necesaria

Se autentican por SHA-256 los originales UCDP Multiple Onset 23.1 y 25.1 y ACD 23.1; el estudio GEO previo está congelado y verificado en CI desde las cuatro ediciones oficiales 23.1, 24.1, 25.1 y 26.1. Antes de leer cualquier dato histórico, se autentican además los cinco archivos/manifiestos originales de pronósticos 2027 y se exige **0 etiquetas resueltas** entre las **424 preguntas país–endpoint**.

El informe completo, data/historical-geo-newconf-annual-residuals.json, se reproduce byte a byte mediante scripts/diagnose_historical_geo_newconf_year_counts.py y el job institucional obligatorio geo_newconf2027_empirical_historical_count_residuals. Tests adversariales garantizan 196 países sin duplicados, horizonte dos años inmutable, ausencia de valores perdidos/imputaciones como cero, series históricas completas, fórmulas algebraicas y que no se utilicen etiquetas 2027.

Para **identificar** dependencia geopolítica real se necesitarían varios años objetivo auténticamente separados, emitidos antes de la publicación de sus resultados, con marginales suficientemente calibradas y metodologías explícitas para controlar shocks temporales, revisiones y paneles de países repetidos. **No** se fija ahora un valor de correlación, un número efectivo de observaciones, p-valores IID ni ninguna corrección de probabilidades 2027.

**Conclusión:** la investigación histórica permite rechazar la lectura ingenua de que «dispersión superior a 1 = correlación geopolítica». Muestra tanto errores de calibración persistentes como variación temporal, pero todavía **no identifica ni valida cuantitativamente la dependencia estructural entre países**.
