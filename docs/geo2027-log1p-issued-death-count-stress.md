# GEO2027 — Certificación de sensibilidad de la sombra LOG1P emitida

**Protocolo de estrés · 16 de noviembre de 2026.** Esta auditoría trabaja **directamente sobre las 196 probabilidades de la sombra prospectiva LOG1P ya emitida**, cuyo archivo canónico conserva el SHA-256 \`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90\` y apareció por primera vez en el commit institucional \`a2af84346bd223d2a105cf727b3462cd0955fdac\`. También verifica el GEO2027 original SHA \`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5\` y las 15 alertas originales SHA \`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb\`.

**No se emite otra predicción:** todos los cálculos son contrafactuales para estudiar estabilidad. No hay etiquetas oficiales completas de 2027.

## Hipótesis de estrés fijada

Para cada país con muertes **best** observadas de violencia organizada estatal \(d\) en el **origen 2025**, se calculan tres escenarios de revisión hipotética del conteo anual: **±1, ±5 y ±10 muertes**, sin ningún ajuste posterior basado en el resultado. Las perturbaciones son enteras, no negativas, y **se recortan dentro de su estado binario original** (0–24 muertes o ≥25); el objetivo es aislar la sensibilidad a la información *que el GEO binario no utiliza*. Una revisión que cruce el umbral de 25 invalida deliberadamente este diagnóstico, porque también cambiaría el estado de entrada y las transiciones del Markov.

Los escenarios **no** son simulaciones Monte Carlo ni percentiles estimados de revisiones reales. No conocemos la probabilidad de que la edición UCDP se revise ±1, ±5 o ±10; tampoco suponemos que futuras revisiones entre países sean independientes en la realidad. Los márgenes se eligen como pruebas algebraicas reproducibles, no como un límite empírico sustentado por UCDP.

Partimos de la forma ya **congelada** al emitir:

\[
p(d)=\sigma\Big(\operatorname{logit}(p_{\rm GEO}^{\rm emitido})
+\beta_0+\beta_I x_I(d)+\beta_A x_A(d)\Big).
\]

Los tres coeficientes son exactamente los valores publicados en el documento 2027, sin volver a ajustar sobre un nuevo archivo: \(\beta=[-0{,}337793886776;\ 1{,}185261838805;\ 1{,}934189190903]\). **Se mantiene fijo el offset del GEO binario original para 2027**. Se reproduce matemáticamente la probabilidad emitida antes de calcular cada banda contrafactual. Las bandas incluyen siempre la probabilidad realmente emitida y se certifican para **cada valor entero admisible de muertes** por monotonicidad del predictor logit dentro de cada estado.

## Certificación matemática

Dentro de un estado fijo (inactivo o activo) la función \(\log(1+d)\) es monótona y la logística también. En consecuencia, los **dos extremos del intervalo de muertes** producen el mínimo y el máximo exactos de \(p(d)\) en el escenario, sin muestreo aleatorio.

Para auditar por una vía independiente se comprueba además la desigualdad de Lipschitz global de la logística, con derivada \(\sigma'(z)=\sigma(z)(1-\sigma(z))\leq1/4\):

\[
p_{\max}-p_{\min}\leq
\frac{|\beta_s|}{4\,N_s}
\left|\log\frac{1+d_{\max}}{1+d_{\min}}\right|,
\quad
N_I=\log(26),\quad N_A=\log(101).
\]

No es una cota de error predictivo ni de incertidumbre histórica: solo una cota algebraica **condicionada a que \(p_{\rm GEO}\) y \(\beta\) permanezcan fijos y el estado de origen no cambie**.

Para cada margen se publican: 196 bandas individuales, media/mediana/P95/máximo de anchura, países con posible cambio ≥1 o ≥5 puntos, cuenta de países para los que el intervalo habría cruzado el umbral pero se ha recortado, y suma de límites inferiores/superiores de las 196 probabilidades. **La suma de límites no es un intervalo de confianza del número de países activos ni un intervalo de predicción.**

## Rankings sin inferir falsos cambios de alertas

En los grupos de riesgo **originalmente inactivos (162 países)** y **activos (34 países)** se estudia *solo* la **ordenación nominal de la nueva sombra**. Como diagnóstico de continuidad con las 15 alertas antiguas, se respeta el mismo tamaño (10 entradas y 5 salidas), pero **no se emite un nuevo top-10/top-5 ni se alteran las alertas originales**.

Para entrada, se ordena por \(p_{\rm activo}\) descendente; para salida, por \(1-p_{\rm activo}\) descendente. Los empates se resuelven con GWNO numérico ascendente. Por cada país con intervalo de puntuación \([L_i,U_i]\):

- **Posible:** aparece entre los k primeros cuando toma su máximo \(U_i\) y todos los rivales su mínimo \(L_j\). Si aun así hay al menos k rivales mejor situados, se certifica su exclusión.
- **Obligatorio:** sigue entre los k primeros cuando toma su mínimo \(L_i\) y todos los rivales su máximo \(U_j\). Si aun así tiene menos de k rivales por delante, se certifica la pertenencia.

Este test es **exacto bajo el conjunto rectangular de perturbaciones independientes** (cada país puede adoptar cualquier conteo admisible simultáneamente con todos los demás). Las restricciones globales que pudieran correlacionar revisiones reales no se incluyen y no deben inferirse de aquí.

## Resultados exactos en la emisión prospectiva registrada

Los **196 países** de la emisión LOG1P han pasado los controles de coherencia con los originales. Distribución de 2025: **154 países con cero muertes**, **8 países entre 1 y 24**, **34 países con 25 o más**. Se comparan *extremos hipotéticos* de 2025, manteniendo fijo el estado y los parámetros del GEO y LOG1P. No son nuevas predicciones, y 2027 sigue sin resultados observados.

| Perturbación admisible en muertes 2025 | Anchura media de \(p_{2027}\) (pp) | Mediana (pp) | P95 (pp) | Máximo (pp) | Países con posible cambio ≥5 pp |
|---|---:|---:|---:|---:|---:|
| **±1**, sin cruzar el estado binario | 0,6502 | 0,3865 | 2,0935 | **4,7143** | 0 |
| **±5**, sin cruzar el estado binario | 2,1294 | 1,2280 | 8,2716 | **13,3181** | 21 |
| **±10**, sin cruzar el estado binario | 3,1780 | 1,8487 | 11,9590 | **18,5354** | 31 |

La métrica «anchura» es el máximo menos el mínimo de la **probabilidad modelo** dentro del intervalo de muertes hipotéticas. No es la magnitud de una revisión realmente ocurrida.

### Burundi: fragilidad intrínseca, sin cruzar 25 muertes

En la **emisión LOG1P real de 2027** para Burundi, las muertes 2025 UCDP son **0** y su probabilidad emitida de superar 25 muertes estatales en 2027 es **22,6212 %**. Si se recalculara solo la función LOG1P con la hipótesis de **10** muertes en 2025, sin modificar ni el estado binario ni los parámetros, sería **41,1566 %**, **+18,5354 pp**. Con **1** muerte sería **27,3355 %**, +4,7143 pp; con **5** muertes, **35,9393 %**, +13,3181 pp.

Este contraste identifica una dependencia matemática de la salida publicada respecto a pequeños cambios dentro de un estado inactivo. **No se ha modificado ninguna de esas probabilidades emitidas.** El caso coincide cualitativamente con el deterioro editorial observado en la reconstrucción histórica Burundi 2022, sin tratarlo como una frecuencia o una probabilidad de revisión futura.

### Certificación exacta de los conjuntos top-k de la sombra

Los grupos de riesgo proceden del estado original 2025: **162 inactivos**, **34 activos**. Se preservan tamaños de referencia 10/5, pero estas listas son **diagnósticos de la sombra**, no una reedición de las 15 alertas GEO originalmente públicas.

| Perturbación en 2025 | Top-10 entrada: puestos **obligatorios** | Países **posibles** en el top-10 | Top-5 salida: puestos **obligatorios** | Países **posibles** en el top-5 |
|---|---:|---:|---:|---:|
| **±1** muerte | 9/10 | 12 | 4/5 | 6 |
| **±5** muertes | **2/10** | 25 | 3/5 | 6 |
| **±10** muertes | **2/10** | **28** | 3/5 | 7 |

Con el escenario ±10, solamente **Chad y Burundi** tienen pertenencia obligatoria al top-10 de entrada de esta sombra bajo cualquier combinación de conteos permitidos. En el top-5 de resolución, los miembros obligatorios son **Togo, Angola e Indonesia**. «Posible» significa que **existe** alguna combinación de perturbaciones para la cual ese país entra en los k primeros; no es una probabilidad de selección y no implica que los 28 posibles puedan ocupar simultáneamente las 10 posiciones.

La certificación solo cubre el **conjunto rectangular hipotético** de revisiones enteras por país. Para **2 países** en ±10, el intervalo sin recortar podría cruzar el umbral de 25; esa porción se ha **excluido** porque invalidaría la suposición de que el modelo Markov binario no cambia.

### Suma de probabilidades bajo perturbaciones simultáneas

La emisión real LOG1P tiene **35,9840** países activos esperados en 2027 (suma de sus 196 probabilidades). La suma de los extremos de sus bandas sería, para los tres escenarios:

| Perturbación | Suma mínima contrafactual | Suma máxima contrafactual |
|---|---:|---:|
| ±1 muerte | 35,9264 | 37,2009 |
| ±5 muertes | 35,6389 | 39,8124 |
| ±10 muertes | 35,4613 | 41,6901 |

**No son intervalos de predicción del número de países activos** ni límites de confianza: sumar 196 bandas deterministas bajo una hipótesis rectangular de revisión produce otra banda determinista, nada más. Las revisiones reales podrían exceder ±10, cruzar el umbral binario o alterar años históricos y coeficientes. Ningún dato de 2027 ha sido puntuado.

**Conclusión:** la fragilidad del predictor continua confirmado por los archivos históricos se manifiesta también en la **emisión 2027 congelada** bajo alteraciones hipotéticas de 2025. El programa debe conservar el archivo prospectivo y evaluar de forma separada (i) Brier/log-loss futuro, (ii) sensibilidad editorial, y (iii) dependencia de decisiones de rankings sin presentar cotas matemáticas condicionadas como calibración.

## Controles de publicación

El script solo lee las emisiones congeladas y sus SHA, y genera un **nuevo informe de diagnóstico**, no un nuevo archivo de pronóstico. GitHub Actions ejecuta pruebas sintéticas de límites, ranking adversarial, empates, no reemisión y reproducción desde la emisión canónica. El despliegue institucional se bloquea si el resultado recalculado no coincide byte a byte con el informe publicado.

**Qué aporta:** identificar países donde un cambio moderado de información puede mover más que el propio margen predictivo y determinar qué miembros de un ranking simulado sobreviven a todos los cambios permitidos. **Qué no aporta:** estimar la distribución de revisiones UCDP, demostrar la calibración de 2027 o justificar modificar el modelo tras inspeccionar sus resultados históricos.

Scripts: \`scripts/audit_geo2027_log1p_issued_death_stress.py\`; pruebas: \`scripts/test_audit_geo2027_log1p_issued_death_stress.py\`; informe exacto: \`data/geo2027-log1p-issued-death-count-stress.json\`.
