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

## Controles de publicación

El script solo lee las emisiones congeladas y sus SHA, y genera un **nuevo informe de diagnóstico**, no un nuevo archivo de pronóstico. GitHub Actions ejecuta pruebas sintéticas de límites, ranking adversarial, empates, no reemisión y reproducción desde la emisión canónica. El despliegue institucional se bloquea si el resultado recalculado no coincide byte a byte con el informe publicado.

**Qué aporta:** identificar países donde un cambio moderado de información puede mover más que el propio margen predictivo y determinar qué miembros de un ranking simulado sobreviven a todos los cambios permitidos. **Qué no aporta:** estimar la distribución de revisiones UCDP, demostrar la calibración de 2027 o justificar modificar el modelo tras inspeccionar sus resultados históricos.

Scripts: \`scripts/audit_geo2027_log1p_issued_death_stress.py\`; pruebas: \`scripts/test_audit_geo2027_log1p_issued_death_stress.py\`; informe exacto: \`data/geo2027-log1p-issued-death-count-stress.json\`.
