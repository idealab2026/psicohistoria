# GEO2027 — Ablación de intensidad: Markov de cuatro estados frente al binario original

**Investigación retrospectiva, 16/11/2026.** Se evalúa la hipótesis de que distinguir la intensidad de las muertes estatales, en vez de convertir inmediatamente todo el pasado a 0/1, puede mejorar la probabilidad de superar el umbral de **≥25 muertes** al cabo de dos años. **No se altera ninguna emisión original GEO2027 ni GEO2028**, sus 15 alertas ni sus protocolos de evaluación prospectiva.

## Diseño fijo antes de conocer el resultado

La referencia es el **Markov de dos estados** original GEO2027, reconstruido sin cambiar ecuaciones: umbral anual 25, global Laplace(1,1), probabilidad local con shrinkage global 20, horizonte H2 y 196 países GWNO por origen.

Se contrapone **una única alternativa definida ex ante**, sin optimización de umbrales ni hiperparámetros contra el resultado histórico:

| Estado Markov propuesto | Muertes anuales state-based, estimación best | Resultado binario oficial |
|---|---|---|
| 0 · Cero | 0 | Inactivo |
| 1 · Bajo | 1–24 | Inactivo |
| 2 · Activo | 25–99 | Activo |
| 3 · Alto | ≥100 | Activo |

La matriz global de transición es 4×4. Cada una de sus cuatro filas utiliza **un pseudoconteo Dirichlet=1 por estado destino**. Cada fila local se contrae hacia su correspondiente fila global con **20 exposiciones**, idéntico al modelo original. La distribución obtenida tras **dos transiciones** desde el estado de origen se suma sobre los estados 2 y 3:

\[
P(Y_{t+2}\geq 25)=\sum_{j=0}^{3}P_{s_t,j}(P_{j,2}+P_{j,3}).
\]

Los umbrales 1, 25 y 100 son una especificación exploratoria única; no se ha demostrado que sean óptimos. La alternativa conserva la distinción entre cero y violencia bajo el umbral, y dentro de la violencia activa entre niveles de 25–99 y ≥100. **No es todavía un modelo continuo de log(1+muertes).**

## Contraste sin fuga de información temporal

| Edición para entrenar (último año) | Edición para observar el resultado | Horizonte | Cohorte |
|---|---|---|---|
| UCDP OrganizedViolenceCY 23.1, **2022** | UCDP 25.1, **2024** | H2 | 196 GWNO |
| UCDP OrganizedViolenceCY 24.1, **2023** | UCDP 26.1, **2025** | H2 | 196 GWNO |

**Regla estricta:** ambos modelos se ajustan *solo* con la edición de origen y años menores o iguales al corte. Las etiquetas del año objetivo se leen *exclusivamente* de la edición posterior tras calcular las probabilidades. No se rellenan resultados ausentes como negativos.

Los cuatro archivos oficiales son exigidos por sus SHA-256 ya controlados en el repositorio. El resultado de la referencia binaria debe reproducir exactamente, dentro de tolerancia numérica 1e-10, los dos Brier/log-loss del informe anterior data/forecast-2027-archival-cross-release.json (**392 países-año, 69 positivos, Brier 0,04008405691286656**). Si no reproduce esos números, se bloquea el nuevo resultado: no hay comparación legítima.

## Métricas y criterios

- **Métrica principal:** diferencia pareada de Brier, valor del modelo de cuatro estados menos el original binario; un valor negativo favorecería al modelo de intensidad.
- **Secundarias:** diferencia de log-loss; cada cohorte por separado; diagnósticos por estado de origen binario y por intervalo de intensidad; número de países con mejor/peor Brier promedio y principales deterioros/mejoras individuales.
- **Inferencia:** dos años objetivo no permiten estimar adecuadamente la dependencia global entre países ni acreditar un intervalo de confianza. No se realizará bootstrap IID por países ni se presentará un promedio de dos años como prueba estadística de superioridad.
- **Sin selección oportunista:** no se reajustan bins ni shrinkage después de mirar el resultado; si la alternativa empeora, se publica ese resultado igualmente. Variantes posteriores requieren nuevo protocolo.

Las versiones 23.1 y 24.1 son archivos oficiales existentes hoy; no existe notarización independiente de su fecha original de publicación y estas predicciones históricas no fueron emitidas en 2022/2023. Es **una reconstrucción ex post separada por versiones**, no validación prospectiva.

## Resultados oficiales, reconstruidos en GitHub Actions

Los cuatro archivos UCDP originales, verificados por SHA-256, producen los **mismos** 392 casos (69 activos) y los **mismos Brier y log-loss** del Markov binario previamente auditado. Resultados de esta única alternativa de cuatro estados, **sin optimizar sobre el holdout**:

| Resultado H2 | Binario GEO original | Cuatro estados de intensidad | Diferencia (4E − 2E) |
|---|---:|---:|---:|
| 2024 · Brier, 196 países | **0,04143146** | 0,04627834 | +0,00484688 |
| 2025 · Brier, 196 países | 0,03873665 | **0,03862031** | −0,00011634 |
| **Total Brier, 392 países-año** | **0,04008406** | 0,04244933 | **+0,00236527** |
| **Total log-loss** | **0,15439774** | 0,15491694 | **+0,00051921** |

**Conclusión con criterio principal:** cuatro estados **empeoran un 5,90 % el Brier retrospectivo agregado** respecto al binario; la ventaja marginal de 2025 no compensa el deterioro de 2024. La diferencia de log-loss también es desfavorable. La ampliación a categorías de intensidad no queda justificada como sustitución del modelo original.

### Segmentación y concentración del error

| Intensidad de origen | Casos en dos cohortes | Variación Brier cuatro estados − binario |
|---|---:|---:|
| 0 muertes | 295 | +0,0003291 |
| 1–24 muertes | 26 | **+0,0280567** |
| 25–99 muertes | 24 | **+0,0212145** |
| ≥100 muertes | 47 | **−0,0086917** |

El modelo de intensidad mejora el subgrupo con **≥100 muertes** en el origen, pero **empeora** los intervalos de **1–24** y **25–99**, precisamente donde el umbral binario de 25 muertes puede afectar las decisiones. Son grupos pequeños y no deben usarse para anunciar reglas generales o reformular el modelo después de mirar el holdout.

A nivel país, **163 de 196** tuvieron menor Brier promedio con cuatro estados, y **33** uno mayor. Esa mayoría no asegura un mejor score: los deterioros de algunos países son grandes. Este es un hallazgo concreto contra la heurística «gana en más países, luego el modelo es mejor»; el promedio de pérdidas cuadráticas atribuye más peso a errores de gran magnitud.

En 2024, el subgrupo de origen activo (37 países) empeora **+0,01595** en Brier; en 2025, el subgrupo activo (34 países) mejora **−0,01440**, lo que explica parte del cambio de signo por año. Dos años y grupos solapados no constituyen una prueba de superioridad para una variante adaptada a 2025.

**Consecuencia para la investigación:** conservar el Markov binario actualmente emitido. Si se plantea un modelo de conteos continuos o un refinamiento de shrinkage, se debe separar entrenamiento/selección de hiperparámetros de una nueva evaluación histórica y registrar de antemano el plan; no optimizar los resultados de estos dos años y presentarlos como validación independiente.

**Ficheros:** scripts/experiment_geo2027_intensity_markov_cross_release.py (reconstrucción, lectura), scripts/test_experiment_geo2027_intensity_markov_cross_release.py (contratos sintéticos) y data/geo2027-intensity-markov-cross-release.json (reporte byte a byte). GitHub Actions impide publicar cuando el resultado no coincide con las fuentes con SHA oficial. Cero resultados 2027 certificados.
