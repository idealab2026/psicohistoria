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
