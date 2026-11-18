# GEO H2 — Sensibilidad al umbral cero en once orígenes históricos

**Estudio retrospectivo · 18/11/2026.** Extensión del experimento 2021 de la PR #123 a una secuencia completa y predeterminada de **11 pseudo-orígenes consecutivos 2012–2022**, todos con horizonte H2 y país-año objetivo **2014–2024**.

## Pregunta falsable

¿Las reclasificaciones UCDP de recuentos cero a 1–24 fallecidos, o viceversa, explican regularmente un cambio de pronósticos del modelo Markov de cuatro estados, o se concentran en 2021/Ruanda?

Se mantienen fijos:
- Mismos 196 GWNO evaluados en cada año; **2.156 país-años de evaluación**, sin tratar los orígenes como fuentes independientes.
- **199 países** de aprendizaje del prior global, sin excluir registros que no pertenezcan a la cohorte evaluada.
- Misma fórmula original de cuatro estados `[0,1–24,25–99,≥100]`, prior Dirichlet(1), shrinkage 20, horizonte dos.
- Ediciones de origen **23.1 versus 24.1** y resultados objetivo **26.1**. Se recorta el aprendizaje a cada año de origen; esto **no vuelve contemporáneo un archivo publicado después**.

## Diseño factorial

Para cada pseudo-origen, todas las revisiones de datos históricos en las dos ediciones oficiales se agrupan en **Z** (cruce 0 ↔ 1–24) y **O** (cualquier otro cambio). Se calculan cuatro probabilidades con el estimador fijo: `00` (fuente antigua), `10` (solo Z), `01` (solo O), `11` (fuente nueva). Las contribuciones Shapley de Z y O se calculan sobre la probabilidad H2 y el Brier con etiqueta objetivo fija. La suma de contribuciones debe recuperar el cambio observado para todos los años y países.

Los puntos extremos `00` y `11` tienen que reproducir exactamente el experimento anterior de **11 años y dos ediciones**, y para pseudo-origen 2021 tienen que reproducir exactamente las 196 probabilidades de la PR #123.

Se informa por año del número de cruces, países modificados directamente, países con reclasificación del **estado inicial**, máxima variación de probabilidad, efecto Brier y propagación indirecta por la matriz global. El informe conserva datos por GWNO, permitiendo reconstrucción y consultas posteriores sin redescargar archivos.

## Limitaciones

Es un análisis de **sensibilidad de datos retrospectivos**. Los años evaluados reutilizan el mismo par de ediciones UCDP 23.1/24.1, con revisiones acumuladas: no son once pares independientes de fuentes, ni ensayos clínicos, ni emisiones auténticas en los pseudo-orígenes. No se selecciona un modelo ganador en función de los resultados. Tampoco se tocan predicciones ni alertas originales GEO2027/GEO2028.

Resultados completos: `data/geo-h2-11-origin-zero-low-sensitivity.json`, sujetos a reproducción SHA y control público institucional antes de integrarlos.

## Resultados reproducidos con archivos oficiales SHA

La ejecución para los **11 pseudo-orígenes 2012–2022 y 2.156 país-años** ha reproducido exactamente las puntuaciones originales para cada edición de fuente y las 196 probabilidades del experimento 2021. El modelo, sus parámetros y las etiquetas de destino 26.1 no han cambiado.

| Origen | Revisiones cero↔baja intensidad acumuladas | Países cuyo estado inicial cruza cero↔baja | Máximo `|Shapley Δp|` |
|---|---:|---|---:|
| 2012 | 4 | Ninguno | 0,1212 pp |
| 2013 | 4 | Ninguno | 5,2540 pp |
| 2014 | 4 | Ninguno | 0,9870 pp |
| 2015 | 4 | Ninguno | 0,1924 pp |
| 2016 | 4 | Ninguno | 0,1258 pp |
| 2017 | 4 | Ninguno | 0,1408 pp |
| 2018 | 4 | Ninguno | 0,1817 pp |
| 2019 | 4 | Ninguno | 0,3085 pp |
| 2020 | 4 | Ninguno | 0,9043 pp |
| 2021 | 5 | Ruanda (517) | 11,2437 pp |
| 2022 | 6 | Burundi (516) | **21,3549 pp** |

En total existen **6 revisiones únicas de recuentos país-año que cruzan de 0 a 1–24 fallecidos** entre UCDP 23.1 y 24.1, acumuladas en el conjunto de los 11 cortes de entrenamiento. La sexta revisión, descubierta al incluir el origen 2022, es **Burundi 2022: 0→10 fallecidos**, que convierte el estado de inicio de cero a baja intensidad.

Para Burundi, origen simulado 2022 y objetivo histórico 2024, la probabilidad de actividad del modelo de cuatro estados cambia de **0,160392165100** a **0,373848182935**. La contribución Shapley del bloque cero↔baja intensidad es **+0,213549341091**, mientras que la suma del efecto de todos los bloques es +0,213456017835. No es una prueba de que el nuevo valor sea más fiable: únicamente revela la inestabilidad que introduce el estado inicial.

En el agregado de los once orígenes, el efecto de los cruces de cero↔baja intensidad sobre Brier con etiquetas 26.1 fijas es **+0,0001161356714**, y el resto de las revisiones aporta **−0,0001638885530**. El cambio neto es **−0,0000477528816**: una mejora media de Brier muy pequeña en la fuente nueva, que coexiste con grandes cambios de probabilidad en casos individuales. Es incorrecto tomar el promedio como prueba de estabilidad por país.

El caso de Burundi con origen 2013 exhibe además una contribución de **−0,052540416585** a la probabilidad debida al bloque cero↔baja. Este es un efecto histórico distribuido sobre sus transiciones locales y el prior; **no** implica que su estado inicial en 2013 haya sido reclasificado.

[Informe íntegro de los 11 años y 2.156 país-años](../data/geo-h2-11-origin-zero-low-sensitivity.json) · [Script reproducible](../scripts/experiment_geo_h2_11origin_zero_low_source_stress.py) · [Pruebas del experimento](../scripts/test_experiment_geo_h2_11origin_zero_low_source_stress.py).

**Limitaciones de inferencia:** los cambios de origen acumulados de 2012 a 2022 no son independientes. Este estudio permite documentar una sensibilidad estructural del estimador a la edición de datos, **no** establecer su habilidad predictiva prospectiva ni ofrecer significación estadística habitual con n=2.156 independiente. La selección de la fuente 24.1 se hizo después de varios orígenes reconstruidos.
