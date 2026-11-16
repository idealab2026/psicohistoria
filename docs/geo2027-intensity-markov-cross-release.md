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

**Ficheros:** scripts/experiment_geo2027_intensity_markov_cross_release.py (reconstrucción, lectura), scripts/test_experiment_geo2027_intensity_markov_cross_release.py (contratos sintéticos) y data/geo2027-intensity-markov-cross-release.json (reporte byte a byte). GitHub Actions impide publicar cuando el resultado no coincide con las fuentes con SHA oficial. Cero resultados 2027 certificados.
