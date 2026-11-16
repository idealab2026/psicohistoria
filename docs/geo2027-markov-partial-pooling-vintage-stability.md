# GEO2027 · Regularización parcial del Markov y estabilidad frente a revisiones UCDP

**Estudio mecanístico registrado el 16/11/2026.** Continuación de la PR #101, que identificó una pérdida de discriminación entre los 154 países sin muertes estatales en el origen de 2025 al eliminar completamente su historial nacional del Markov. El objetivo aquí **no es escoger otro modelo ni emitir probabilidades para 2027**, sino identificar la relación entre cantidad de historia local, heterogeneidad del riesgo y sensibilidad a revisiones de fuentes.

## Hipótesis y diseño predeterminados

La primera emisión original GEO2027 utiliza un Markov de dos estados: actividad estatal anual UCDP con umbral `sb_total_deaths_best >= 25`, prior mundial Laplace-1, y mezcla de transiciones propias con un prior mundial equivalente a **20 observaciones**. La sombra global-only posterior prescinde de esas transiciones locales; su ventaja potencial es transferibilidad, pero comprime la diferenciación geográfica del riesgo.

Para cada país \(c\) y estado \(s\), se define el prior mundial **excluyendo las transiciones del propio país**:

\[
g_s^{(-c)}=\frac{N_{s\rightarrow1}-n^c_{s\rightarrow1}+1}
                   {N_s-n^c_s+2}.
\]

El núcleo de prueba es \[
q_s^{(c,w)}=\frac{w\,n^c_{s\rightarrow1}+20g_s^{(-c)}}{w\,n^c_s+20},
\qquad w\in\{0,\;0.25,\;0.5,\;1\}.
\]

El pronóstico bruto Markov a **dos pasos** desde el estado binario \(s_o\) de origen es \((1-q_{s_o})q_0+q_{s_o}q_1\). Los cuatro valores de \(w\) son **una rejilla exploratoria fija de sensibilidad**, no un conjunto para escoger según Brier ni emisiones de nuevas probabilidades por país. \(w=0\) es global-only puro, y \(w=1\) reintroduce el historial local completo, aunque **no coincide exactamente con GEO original**, cuyo prior mundial sí incluía al propio país. El script reconstruye **por separado** la ley matemática exacta del GEO original y exige coincidencia de sus 196 pronósticos publicados de 2027.

El peso relativo de información histórica local para estado \(s\) queda representado por \(\frac{wn^c_s}{wn^c_s+20}\). No es una confianza estadística ni un intervalo posterior: es la proporción algebraica de contribución nacional introducida por el pseudoconteo. Se publican exposiciones históricas por estado y el número de países sin transiciones estatales activas, para distinguir escasez de datos de cambios de probabilidad.

## Tres cortes históricos y cuatro fuentes oficiales

Se descargan exclusivamente ediciones **SHA-256 fijadas** de UCDP OrganizedViolenceCY:

- Origen **2022**, con ediciones oficiales **23.1, 24.1, 25.1, 26.1**.
- Origen **2023**, con ediciones **24.1, 25.1, 26.1**.
- Origen **2025**, con la única edición que llega a ese año: **26.1**.

Son **8 combinaciones origen–edición** y **5 comparaciones solapadas de revisiones**, no muestras independientes. Al comparar una edición antigua y otra posterior, **se cortan todas las transiciones y estados hasta el mismo año de origen**, aunque la edición posterior haya revisado retrospectivamente los conteos. Ninguna transición de 2026 ni 2027 participa en la evaluación de 2025. Si falta el año de origen de alguno de los 196 GWNO, se suspende el experimento; no se codifica ausencia como cero.

Para cada peso y edición se calcula la distribución de probabilidades Markov **solo como diagnóstico agregado**, separada por muertes observadas en el origen (cero, 1–24 y 25 o más). Interesan especialmente el rango, dispersión y percentiles de los **154 países sin muertes en 2025**. La sensibilidad editorial se resume mediante media, percentil 95 y máximo de cambios **absolutos** de probabilidad, además de contar países que cambian estado binario entre ediciones. Se registran únicamente ejemplos de países con mayor sensibilidad del componente histórico, **sin publicar una nueva tabla de predicciones nacionales de 2027**.

Esta es una comparación de **probabilidades Markov brutas**, no del modelo LOG1P recalibrado. **No se compara directamente su Brier con el de modelos calibrados**, ni se pretende que la regularización intermedia gane un forecast prospectivo. Recalibrar las variantes y seleccionar \(w\) usando los mismos objetivos históricos ya inspeccionados sería una elección retrospectiva adicional.

## Criterio de interpretación

**Mayor dispersión no significa mayor capacidad predictiva.** Puede indicar extracción de información de persistencia nacional o, por el contrario, sobreajuste a historias locales revisables. Del mismo modo, menos variación al revisar fuentes no equivale a menor Brier futuro. Por eso se publican ambas dimensiones **sin optimizarlas mediante un score compuesto**.

La exactitud de la emisión original se verifica con el SHA original GEO2027 (`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`), la sombra LOG1P (`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`), la nueva sombra global-only (`251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697`) y las 15 alertas originales (`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`). **Cero resultados oficiales de 2027 resueltos, cero nuevos pronósticos o alertas**. Las versiones históricas no son series temporalmente disponibles tal cual en los años a los que se aplican: pueden incluir correcciones editoriales retroactivas.

**Código:** `scripts/diagnose_geo2027_markov_partial_pooling.py`. **Tests:** `scripts/test_diagnose_geo2027_markov_partial_pooling.py`. **Informe reproducible:** `data/geo2027-markov-partial-pooling-vintage-stability.json`. GitHub Actions reproduce el estudio con los cuatro archivos oficiales y exige igualdad byte a byte antes de publicación.
