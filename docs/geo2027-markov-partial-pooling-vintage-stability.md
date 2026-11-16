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

## Resultados reproducidos: 196 GWNO, cuatro versiones SHA-verificadas

El script reconstruye **8 bloques origen–edición** y **5 comparaciones de revisión**. En el origen real de emisión **2025**, se certifica que los 196 pronósticos GEO Markov originales se reproducen exactamente con la ley original (historia local y contribución propia al prior global). Todos los grupos muestran datos directamente observados: **154 países con 0 muertes**, **8 con 1–24** y **34 con ≥25**.

### ¿Cuánto riesgo geográfico diferencia la historia local?

Para los **154 países con cero muertes en 2025**, las siguientes probabilidades son **brutas del componente Markov H2**, sin recalibración LOG1P, derivadas solo de información hasta 2025. No son cuatro nuevas emisiones para 2027.

| Multiplicador local \(w\) | Media del riesgo Markov H2 | Desviación típica poblacional | Rango máximo − mínimo |
|---|---:|---:|---:|
| **0: sin historial local** | 5,315 % | 0,035 pp | **0,211 pp** |
| **0,25** | 4,622 % | 1,922 pp | **11,204 pp** |
| **0,5** | 4,274 % | 3,055 pp | **18,445 pp** |
| **1: historia local plena** | 3,924 % | 4,321 pp | **27,102 pp** |

**Lectura correcta:** al aumentar \(w\), aumenta rápidamente la variación entre países con el mismo estado de origen. No se puede inferir que 27 pp de rango sea *mejor pronóstico* que 0,21 pp. El nivel medio también cambia porque parte del historial nacional reduce el riesgo bruto frente al prior mundial.

**Información nacional efectiva:** entre estos 154 países, el peso algebraico medio de las transiciones locales **desde el estado inactivo** con \(w=1\) es **62,25 %** (mediana **64,29 %**). La fórmula es \(n^c_0/(n^c_0+20)\). Es una propiedad del estimador, no una certeza epistemológica de que los datos sean verdaderos ni un posterior estadístico formal. El componente local aumenta mucho más la heterogeneidad en el grupo de 0 muertes de 2025 que el prior global-only.

La diferencia de probabilidad H2 entre usar \(w=1\) y \(w=0\) alcanza **23,88 pp para Burundi** y **18,92 pp para Senegal**. Se publican sus exposiciones de transición y la diferencia absoluta, **no un nuevo listado nacional de emisiones futuras**. Estas diferencias son del Markov bruto; no deben confundirse con las de la comparación de sombras LOG1P calibradas.

### Coste de la revisión histórica

En todas las parejas de revisiones, los 196 países conservan el mismo **estado binario de origen**: ninguna corrección cruza el umbral de 25 en el origen. No obstante, revisiones de **otros años anteriores al origen** sí cambian sus transiciones históricas y pueden alterar la probabilidad.

| Origen y versiones comparadas | Muertes del año de origen revisadas (países) | Cambio medio absoluto con \(w=0\) | Cambio medio absoluto con \(w=1\) | Cambio máximo \(w=0\) | Cambio máximo \(w=1\) |
|---|---:|---:|---:|---:|---:|
| 2022 · 23.1 → 24.1 | 22 | 0,028 pp | 0,046 pp | 0,136 pp | **3,559 pp** |
| 2022 · 23.1 → 25.1 | 24 | 0,053 pp | 0,096 pp | 0,219 pp | **5,260 pp** |
| 2022 · 23.1 → 26.1 | 25 | 0,064 pp | 0,130 pp | 0,409 pp | **5,356 pp** |
| 2023 · 24.1 → 25.1 | 20 | 0,023 pp | 0,061 pp | 0,110 pp | **5,115 pp** |
| 2023 · 24.1 → 26.1 | 20 | 0,067 pp | 0,104 pp | 0,296 pp | **5,206 pp** |

La media del cambio absoluto aumenta con el peso local en **estas cinco parejas**, y el mayor cambio individual también. Pero **el percentil 95 no aumenta siempre**: en la pareja 2022 (23.1→26.1), cae de **0,307 pp con \(w=0\)** a **0,257 pp con \(w=1\)**, mientras el máximo salta de **0,409 a 5,356 pp**. Es decir, la **cola extrema** puede ser más sensible a la historia nacional aunque una medida robusta de centro de distribución mejore. Este matiz impide declarar una «relación universal» entre todo indicador de sensibilidad y \(w\).

Las cinco comparaciones se solapan tanto por países como por archivos fuente; no se agregan sus 980 casos de forma IID ni se estima un intervalo de confianza convencional. El uso de ediciones publicadas después del año de origen impide tratarlo como un historial de pronósticos realmente emitidos.

### Consecuencia metodológica

Hay evidencia estructural de que una regularización intermedia (\(w=0,25\)) **recupera parte sustancial de la discriminación** con sensibilidad media editorial menor que \(w=1\), pero las fuentes examinadas no permiten saber si esa diferenciación es información útil o ruido. Tampoco ofrecen una razón científica para declarar \(w=0,25\) óptimo: elegirlo después de observar estas cinco comparaciones y los Brier retrospectivos previos sería otra selección post hoc.

**Decisión:** no emitir un cuarto nuevo modelo 2027 ni modificar ningún pronóstico ya congelado. Antes de entrenar y emitir otro candidato hay que justificar qué parte de la persistencia nacional tiene señal fuera de las fuentes revisadas y especificar por adelantado cómo se comprobaría su calibración. El primer contraste prospectivo permanece fijado entre la sombra global-only α1 ya emitida y la sombra LOG1P original, usando las 196 etiquetas oficiales completas de 2027 cuando estén disponibles.

## Criterio de interpretación

**Mayor dispersión no significa mayor capacidad predictiva.** Puede indicar extracción de información de persistencia nacional o, por el contrario, sobreajuste a historias locales revisables. Del mismo modo, menos variación al revisar fuentes no equivale a menor Brier futuro. Por eso se publican ambas dimensiones **sin optimizarlas mediante un score compuesto**.

La exactitud de la emisión original se verifica con el SHA original GEO2027 (`5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`), la sombra LOG1P (`52686923315854557a796f8f192d376dab77a4e03b14c1aeb6b4091e48104f90`), la nueva sombra global-only (`251595a12758e006cf21dabbb9771e10b5961c469a5317d6b2b1c5de227f3697`) y las 15 alertas originales (`309b4f270e1d0d6382b7a90ae64c28d7621f96fbf3177a45aaebbffb0f958acb`). **Cero resultados oficiales de 2027 resueltos, cero nuevos pronósticos o alertas**. Las versiones históricas no son series temporalmente disponibles tal cual en los años a los que se aplican: pueden incluir correcciones editoriales retroactivas.

**Código:** `scripts/diagnose_geo2027_markov_partial_pooling.py`. **Tests:** `scripts/test_diagnose_geo2027_markov_partial_pooling.py`. **Informe reproducible:** `data/geo2027-markov-partial-pooling-vintage-stability.json`. GitHub Actions reproduce el estudio con los cuatro archivos oficiales y exige igualdad byte a byte antes de publicación.
