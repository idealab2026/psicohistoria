# ACD2027 — Sensibilidad exacta a dependencia entre países

**Investigación científica · 13 de noviembre de 2026.** Todos los cálculos se derivan de los **32 pronósticos ACD2027 emitidos públicamente en 2026** para el objetivo de 2027 y de su SHA-256 original. Se autentican también las otras primeras emisiones GEO2027, NEWCONF2027, shadow y alertas; sus **424 preguntas país–endpoint** continúan intactas. **Cero resultados de 2027 observados**.

## 1. Por qué 32 observaciones no implican 32 replicaciones independientes

El año 2027 aporta un **único panel anual de 32 países** para ACD, condicionado a que esos países registraran conflicto intraestatal UCDP/PRIO ACD tipo 3/4 en 2025. Los conflictos pueden compartir factores transnacionales, temporales o regionales; los registros ACD pueden compartir cambios de codificación. No conocemos todavía la distribución conjunta de los desenlaces futuros.

Tampoco se puede estimar una matriz fiable de dependencia únicamente mediante las cuatro cohortes históricas adyacentes **2021–2024**: son solo cuatro años objetivo; de 42 países históricos, 37 reaparecen, y el diagnóstico previo reveló inversión de la ventaja de lag1 al cambiar el periodo o condicionar la cohorte a los países de ACD2027. Esos hechos alertan del problema de validación, pero **no estiman una correlación de 2027**.

## 2. Qué se calcula, sin asumir independencia real

Para las probabilidades primeras p_i del modelo principal p_global_recent5 y q_i de un comparador secundario p_lag1_group o p_country_eb, el diferencial Brier de los 32 países es

\[
D = \frac{1}{32}\sum_{i=1}^{32}\left[(q_i-Y_i)^2-(p_i-Y_i)^2\right]
  = c + \sum_{i=1}^{32}a_iY_i,\quad
a_i=-\frac{2(q_i-p_i)}{32}.
\]

**D positivo favorece al principal; D negativo favorece al secundario.**

Para estudiar incertidumbre hacemos **dos mundos contrafactuales separados**: (A) las verdaderas probabilidades marginales de los resultados son exactamente p_i; (B) son exactamente q_i. **No hay evidencia de que ninguno de estos mundos sea verdadero.** En cada uno mantenemos fijas esas probabilidades marginales y calculamos dos estructuras de dependencia:

- **Independencia condicional imaginaria** entre los 32 países. La varianza analítica sería \(\sum_i a_i^2 r_i(1-r_i)\), donde r_i es la marginal de ese mundo.
- **Máxima varianza alcanzable entre todas las distribuciones conjuntas** de 32 variables Bernoulli con las mismas r_i. Se construye con una única variable uniforme U: si a_i ≥ 0 se define Y_i=1 cuando U < r_i; si a_i < 0 se define Y_i=1 cuando U > 1-r_i. Los términos ponderados a_iY_i quedan ordenados conjuntamente. Se alcanzan simultáneamente las cotas de Fréchet que maximizan las covarianzas ponderadas de todas las parejas. Por tanto, su varianza es un **máximo exacto**, no solo un ejemplo de shock fuerte.

**Importante:** el escenario de independencia **no es necesariamente una cota mínima**. El máximo puede mezclar correlaciones positivas y negativas entre distintos países. Ambas estructuras son hipótesis de sensibilidad, no mediciones ni estimaciones de la distribución geopolítica futura. No es lícito utilizar el incremento de varianza para informar un p-valor o un «tamaño muestral efectivo» empírico.

La esperanza es \(\mathbb{E}D=+\sum(q_i-p_i)^2/32\) si p_i son las marginales verdaderas, o la negativa correspondiente si q_i son las verdaderas. Esta identidad se cumple bajo **cualquier** dependencia con esas marginales; no establece quién está calibrado.

## 3. Resultados exactos

| Comparador | Mundo hipotético de marginales verdaderas | E[D] | SD independencia | SD máxima | Varianza máxima / independiente |
|---|---|---:|---:|---:|---:|
| lag1 | p_global_recent5 | +0,00318378 | 0,00693874 | 0,01432985 | **4,265×** |
| lag1 | p_lag1_group | −0,00318378 | 0,00984126 | 0,01501559 | **2,328×** |
| country-EB | p_global_recent5 | +0,00624061 | 0,00971456 | 0,03524046 | **13,159×** |
| country-EB | p_country_eb | −0,00624061 | 0,01108853 | 0,03629429 | **10,713×** |

SD = desviación típica del **diferencial de puntuación Brier entre modelos**, no incertidumbre de la probabilidad de conflicto de un país. Los multiplicadores se refieren a **varianzas**; para SD se toma raíz cuadrada. Los intervalos no son bandas de confianza inferencial.

**Hallazgo:** incluso bajo unas marginales que favorecieran en esperanza al modelo principal, una dependencia conjunta admisible podría multiplicar la varianza de la comparación hasta **4,27 veces** para lag1 y **13,16 veces** para country-EB frente al mundo independiente. La misma puntuación observada en un solo año sería evidencia mucho menos concluyente si existen shocks compartidos importantes.

## 4. Un resultado sorprendente: acertar la media no garantiza ganar en el año

El modelo lag1 ACD2027 tiene exactamente **31 países con las mismas probabilidades** y un país singular, **Sudán del Sur (GWNO 626)**, cuya actividad en 2024 difiere. Esto permite calcular sin simulaciones ni aproximaciones una distribución contrafactual de resultados, bajo el supuesto explícito de independencia, mediante **Binomial(31, r_otros) + Bernoulli(r_SudánSur)**.

| Hipótesis contrafactual | Probabilidad *hipotética* de que gane principal si países independientes | Si la dependencia maximiza la varianza |
|---|---:|---:|
| Marginales del principal p correctas | 85,907 % | 85,920 % |
| Marginales de lag1 q correctas | **54,595 %** | **54,612 %** |

**Lectura:** incluso si las probabilidades marginales de lag1 fueran las verdaderas, el modelo principal podría ganar el diferencial de Brier de **ese único año** en ~54,6 % de las realizaciones bajo estas construcciones concretas. No hay contradicción: lag1 tendría mejor puntuación **esperada** (−0,003184), pero la distribución de la ventaja es asimétrica debido a Sudán del Sur. Esto demuestra por qué ganar un año tampoco establece cuál modelo tiene mejores probabilidades verdaderas.

Estas cifras **NO son probabilidades de que un modelo real vaya a ganar**: dependen de suponer ya correctas unas marginales desconocidas y de adoptar una distribución conjunta no observada. No son predicciones, índices de confianza ni resultados empíricos.

Para country-EB, cuyas diferencias varían mucho por país, se calcula la varianza exacta bajo independencia y la distribución completa del escenario extremo, sin inventar probabilidades de ranking bajo independencia difíciles de enumerar exactamente. El JSON conserva todos los átomos de la construcción extrema y los 64 casos analíticos de lag1 bajo independencia.

## 5. Límite inferencial y contrato científico

1. Mantener **p_global_recent5** como modelo principal ACD2027 y lag1/EB como comparadores exploratorios. Todos los modelos fueron emitidos originalmente con probabilidades y fechas fijas; ninguna se cambia.
2. Cuando se publique la primera fuente oficial completa válida para 2027 (no antes de 2028), aplicar el contrato existente de cobertura, etiquetas y métricas; el evaluador ya rechaza diferencias Brier fuera de la frontera exacta preregistrada por número de países.
3. Comunicar el resultado de 2027 como **un panel anual conjunto**. No aplicar p-valores IID a 32 países ni derivar «significancia» del número nominal de países. No atribuir habilidad generalizable a un solo año ni promocionar automáticamente modelos.
4. Para estimar dependencia temporal y validar superioridad se necesitarán **múltiples años objetivo nuevos**, cada uno emitido antes de sus resultados, misma definición de endpoint, suficientes cambios de contexto, fuentes auditadas y robustez por bloques temporales y grupos de países. La presente investigación **no proporciona** esa validación ni una estimación del número de futuros años necesarios.
5. No agrupar GEO2027, NEWCONF2027 y ACD2027 como 424 realizaciones independientes de un mismo fenómeno, ya que comparten países/años y son objetivos distintos.

## 6. Trazabilidad y reproducibilidad

- Código: scripts/diagnose_acd2027_dependence_variance.py.
- Resultado numérico completo congelado: data/acd2027-dependence-variance.json. Se reproduce byte a byte autenticando las primeras emisiones y sus SHA-256; no contiene etiquetas de 2027.
- Pruebas: scripts/test_diagnose_acd2027_dependence_variance.py, incluyendo test analítico de Fréchet para cargas positivas y opuestas, caso de **32× varianza** con dependencia perfecta e igual peso, cálculo binomial exacto 31+1, esperanza, normalización de masas y validación adversarial.
- Job obligatorio de despliegue: acd2027_dependence_variance, bloquea la publicación si los archivos originales o el resultado derivado cambian.
- Estudios que contextualizan el problema: docs/acd2027-historical-transferability.md, docs/acd-historical-country-influence.md y docs/acd2027-exact-count-prospective-evidence.md.

**Ningún resultado de 2027 ha sido observado, simulado como evidencia, ni utilizado para cambiar el modelo principal.** Los escenarios expuestos son modelos matemáticos explícitos de dependencia bajo supuestos contrafactuales.
