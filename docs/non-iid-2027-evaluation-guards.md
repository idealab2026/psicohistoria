# GEO2027 + NEWCONF2027 — Eliminación de inferencia IID por países

**Revisión metodológica · 15 de noviembre de 2026.** Corrección prospectiva realizada antes de disponer de etiquetas oficiales 2027. No modifica las dos emisiones originales, sus 196 probabilidades por país, el año objetivo, los comparadores, ni la elección de modelos.

## 1. Error corregido

Los evaluadores futuros de GEO2027 y NEWCONF2027 incluían un bootstrap con reposición de **países individuales**, y etiquetaban los percentiles del remuestreo como intervalos del 95 % de la diferencia de Brier.

Este diseño **no permite justificar una incertidumbre frecuentista válida**: los 196 países pertenecen al mismo año, reciben shocks geopolíticos compartidos y **no son una muestra IID** de 196 realizaciones independientes. Volver a muestrear países con reposición construye una pseudopoblación bajo un supuesto de intercambiabilidad que no se ha demostrado.

Los evaluadores han dejado de invocar y contener las funciones bootstrap_interval y bootstrap_delta. No se limita la presentación gráfica: se impide generar el número.

Por compatibilidad con lectores históricos, los campos JSON:
- GEO2027: interval_delta_brier_model_minus_baseline;
- NEWCONF2027: bootstrap_country_delta_brier_95pct;

permanecen como **null incluso si en el futuro existen 196/196 etiquetas**. Se añaden los indicadores iid_country_bootstrap_disabled=true y confidence_interval_justified_by_country_independence=false. No se reemplazan por otro intervalo estadístico injustificado.

## 2. Sustitución que sí es matemáticamente válida: identificación parcial exacta

El objetivo **primario** de comparación de cada cohorte es la diferencia media de Brier entre dos vectores de probabilidades **fijados en la primera emisión**:

\[
D = \frac{1}{N}\sum_{i=1}^{N}\left[(p_i-y_i)^2-(q_i-y_i)^2\right],\quad N=196.
\]

Su denominador es siempre **196**, no el número de países que han recibido etiqueta. Para un país aún sin etiqueta, sus dos contribuciones posibles están completamente determinadas:

\[
d_i(0)=p_i^2-q_i^2,\qquad
d_i(1)=(1-p_i)^2-(1-q_i)^2
\]
\[
d_i(1)-d_i(0)=-2(p_i-q_i).
\]

Si \(O\) es el conjunto de países con etiqueta observada y \(U\) los **ausentes**, entonces el rango exacto de valores de **D sobre las 196 unidades originales** es:

\[
L=\frac{\sum_{i\in O}d_i(y_i)+
       \sum_{i\in U}\min\{d_i(0),d_i(1)\}}{196},\qquad
H=\frac{\sum_{i\in O}d_i(y_i)+
       \sum_{i\in U}\max\{d_i(0),d_i(1)\}}{196}.
\]

**Estas cotas son matemáticamente sharp:** existen asignaciones binarias a las etiquetas desconocidas que alcanzan exactamente ambos extremos. La prueba se obtiene escogiendo, país por país, la etiqueta correspondiente al mínimo (o al máximo), sin necesidad de una estructura de dependencia entre resultados.

Esto define un **conjunto de identificación con etiquetas faltantes**, NO un intervalo de confianza, intervalo predictivo, probabilidad de que gane un modelo ni p-valor. La dependencia no invalida el conjunto: se consideraron **todas** las asignaciones binarias compatibles. Si posteriormente se imponen restricciones empíricas entre eventos, habría que justificar tales restricciones antes de estrecharlo.

Cuando hay **196/196 resultados explícitos**, \(U\) está vacío y las cotas colapsan en **un solo valor**: la diferencia Brier observada para ese año, que sigue sin ser una inferencia sobre capacidad predictiva generalizable. Cuando hay solo 187 etiquetas, el rango refleja todos los valores posibles de las 9 pendientes y evita convertir silenciosamente esas ausencias en ceros.

## 3. Reglas de puntuación y salvaguardas

| Cohorte | Cálculo exploratorio permitido | Fuente completa para evaluación certificable | Inferencia IID |
|---|---:|---:|---|
| GEO2027 | ≥187/196 resultados explícitos | 196/196 + auditoría oficial | **Desactivada** |
| NEWCONF2027 | ≥187/196 resultados explícitos | 196/196 + auditoría oficial | **Desactivada** |
| ACD2027 | 32/32 códigos válidos + controles propios | 32/32 + auditoría de ausencias y fuente | No se introduce bootstrap IID |
| GEO2028 | 196/196 etiquetas explícitas | 196/196 + auditoría oficial | Ya no lo utilizaba |

Los cálculos Brier descriptivos para GEO2027/NEWCONF2027 con ≥187 etiquetas **mantienen la denominación de exploratorios y su propio denominador observado**; se muestran por separado del rango **[L,H] de las 196 preguntas originalmente emitidas**. No debe tomarse el score parcial por una estimación insesgada del full-cohort Brier sin un mecanismo de datos faltantes justificado.

El calculador genérico scripts/paired_brier_partial_identification.py aplica exactamente el álgebra anterior, valida IDs únicos y probabilidades estrictamente interiores, prohíbe etiquetas diferentes de 0/1 y no imputa, remuestrea ni fabrica futuros. Los tests incluyen la **enumeración exhaustiva de todas las completaciones binarias** en un conjunto sintético pequeño y comprobaciones de continuidad para el conjunto 196/196.

Los controles de CI y el registro unificado de cuatro cohortes exigen que no existan funciones de bootstrap IID en ninguno de los dos evaluadores 2027 y que los resultados oficiales continúen pendientes. El SHA-256 de las emisiones, sus primeros commits y los 620 interrogantes permanecen intactos.

## 4. Qué investigación falta para hablar de incertidumbre estadística

La sensibilidad ex ante a dependencias extremas (estudios anteriores sobre ACD/GEO/NEWCONF) **no** estima una copula de resultados reales ni autoriza a sustituir automáticamente el bootstrap por un supuesto shock común. Tampoco se deben reemplazar los intervalos por cluster-robust SE países: un único año objetivo tiene una sola realización temporal y desconocemos la estructura de shocks.

La prueba prospectiva requiere, entre otras cosas, fuentes originales con etiquetas futuras verificadas, cohortes emitidas en **diferentes años de origen** antes de observar esas etiquetas y una evaluación temporal con dependencias justificadas. Hasta entonces, informar diferencias Brier realizadas y cotas de identificación es técnicamente correcto; **inventar intervalos de confianza sería otorgar una precisión estadística inexistente**.

**Estado de resultados 2027/2028 al aprobar esta corrección: cero etiquetas certificadas y ninguna superioridad predictiva demostrada.**
