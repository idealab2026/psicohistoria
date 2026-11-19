# Q-CANDIDATE · Grid de reactivaciones estatales por severidad (19-11-2026)

**Prerregistro de contraste exploratorio, anterior a este cálculo. Sin emisión prospectiva.**

## Objetivo: salir del cuello de botella de 1/505 cruces a 30 días

El objetivo ≥25 muertes estatales observadas en UCDP Candidate produjo solo una
entrada de 505 país-años subumbral a 30 días en 2024–2026. Un buen Brier
global describe continuidad pero no garantiza detectar **reactivación**.

Esta prueba no busca el umbral más favorable a posteriori. Examina **cuatro
estimandos diferentes, fijados antes del cálculo**: un país cuyo Q1 tiene
menos de T muertes estatales `best`, con T∈{1,5,10,25}, supera T muertes
estatales registradas en una ventana futura de 30/90 días. Es una
**reactivación respecto a la intensidad Q1**, no el nacimiento de un
conflicto, ni del todo una predicción de daños reales. La definición de
evento conserva estrictamente `type_of_violence=1`, `date_prec∈{1,2}`,
`date_start>=window_start`, `date_end<=window_end`; no se prorratean
muertes de eventos que atraviesan el límite. Ninguna edición Candidate
tiene obligación de registrar todos los acontecimientos reales.

## Fuentes y años (prefijados)

Archivos oficiales Candidate acumulados enero–marzo Q1 y enero–septiembre
Q3 para **2021, 2022, 2024, 2025, 2026** (10 archivos). Todos
figuran en el catálogo histórico UCDP:
<https://ucdp.uu.se/downloads/olddw.html>.

Se excluye 2023 de la comparación principal porque el catálogo de
acumulados presenta una versión enero–**abril** `23.01.23.04`, no
el mismo `YY.01.YY.03` Q1 usado en los demás años. Concatenar
mensuales de 2023 sin fijar las revisiones produciría una fuente
heterogénea y riesgo de duplicados. 2020 anterior a la cobertura
global anual completa también se excluye.

Para años y = 2021,22,24,25,26:
- **Origen:** Q1 (enero–marzo); el último `date_end` observado será 31/03.
- **Emisión hipotética:** 30/04, NO certificada en la cronología original.
- **Target 30 días:** 01/05–30/05; 90 días: 01/05–29/07.
- **Etiquetas:** versión Q3 provisional de ese mismo año, nunca GED anual.
- **Universo:** los 196 códigos `country_id` de GEO2027 ya
  congelados. Se reutiliza únicamente el universo, sin tocar
  sus probabilidades ni protocolos.

Los SHA y cantidades de 2024–2026 deben coincidir con los resultados
preexistentes de la PR #146. Los SHA de 2021–2022 serán fijados y
verificados con los bytes originales antes de congelar los resultados.
Campos anómalos como `date_prec=0` se cuentan y **excluyen**; fechas
desconocidas o eventos multidiarios que atraviesan fronteras se excluyen.
Los países sin umbral documentado no se declaran libres de violencia.

## Modelos y métricas, sin optimización posterior

**Train:** solo 2021, 2022, 2024 y 2025 (4 cohortes), separando por
T y por horizonte. **Holdout:** 2026, sin entrenamiento con sus etiquetas.
Esto sigue siendo una reconstrucción histórica no certificada as-of;
la investigación ya conoce resultados anteriores de 2026 para el umbral
25, así que no es un experimento totalmente ciego.

Para cada población a riesgo (`muertes estatales Q1<T`) comparar
**cuatro modelos calibrados**, congelando suavizado `k=20`:
1. `climatology`: `(n_pos+1)/(n+2)` en los años de train.
2. `state_recency`: cuatro bins del Q1 estatal
   `0`, `1–4`, `5–9`, `10+`, con
   `(positivos_bin+20*p_global)/(n_bin+20)`.
3. `other_violence`: presencia (≥1 muerte `best` en Q1)
   de violencia no estatal (`type=2`) o unilateral
   (`type=3`), mismo suavizado.
4. `combined`: bin de Q1 estatal × presencia de violencia
   tipo2/3, mismo suavizado. **Es una interacción empírica
   exploratoria**, no un modelo causal.

Se elegirán los bins, umbrales y k sin consultar resultados 2026 de
este nuevo grid. Los modelos pueden tener grupos sin ejemplos;
en tal caso la predicción vuelve exactamente a climatología.
No se reetiquetan grupos ni se modifica k para mejorar el resultado.

Informar **por T y horizonte** de: riesgo 2026, n positivos, prevalencia,
Brier, log-loss, predicción media y **alertas top10 con corrección
de empates** (aciertos mínimo, máximo y esperanza de desempate
uniforme). No interpretar ordenamiento por código país como habilidad.
Reportar las tasas anuales por grupo 2021, 2022, 2024, 2025 y 2026
para detectar cambios estructurales. Comparar climatología sin
extrapolar métricas a verdaderos conflictos.

Reproducibilidad: hash SHA-256 de 10 CSV originales, SHA del
universo canónico, recuentos de exclusión, modelo entrenado completo
y 196 vectores retrospectives 2026 con totales `best` y variables
de entrada. CI debe recomputar los resultados con los bytes oficiales;
cualquier diferencia, incluso en uno de los 10 SHA, detiene la ejecución.

## Resultados reales: cinco años de datos originales y 2026 retenido para evaluación

El experimento se ha ejecutado con **10 archivos originales** UCDP Candidate,
con hashes verificados de 2024–2026 contra estudios anteriores y
cuatro hashes nuevos para 2021–2022. La CI exige reproducción exacta del
[resultado JSON congelado](../data/candidate-reactivation-threshold-grid.json),
con parámetros entrenados de 2021, 2022, 2024, 2025, métricas
2026 y las 196 filas originales de ese año. Ninguna fecha original de
publicación ha sido certificada individualmente.

### Tamaño efectivo de la muestra de eventos nuevos

| Umbral futuro T, muertes `best` estatales | Train 2021/22/24/25: positivos 30d / riesgo | 2026: positivos 30d / riesgo | Train: positivos 90d / riesgo | 2026: positivos 90d / riesgo |
|---|---:|---:|---:|---:|
| ≥1 | 11 / 598 | 0 / 145 | 29 / 598 | 4 / 145 |
| ≥5 | 10 / 642 | 2 / 155 | 25 / 642 | 3 / 155 |
| ≥10 | 7 / 661 | 1 / 159 | 22 / 661 | 2 / 159 |
| ≥25 | 3 / 688 | 0 / 166 | 12 / 688 | 2 / 166 |

**Estas ocho preguntas tienen denominadores distintos**: a menor T,
menos países cumplen la condición `Q1_state_best<T`. Las diferencias
de observación se refieren a datos provisionales Candidate, no a guerra
o víctimas definitivas. Los años de entrenamiento tampoco son independientes
por país, geografía ni conflicto.

### Brier 2026: global, solo violencia estatal reciente, señal de otras violencias e interacción

Cada celda contiene `Brier climatología → Brier modelo combinado` (menor
es mejor). Los otros dos modelos y sus log-loss están disponibles en el JSON
congelado. Ningún resultado se usa para reentrenar o escoger k.

| T | 30 días: global → combinado | 90 días: global → combinado |
|---|---:|---:|
| ≥1 | 0,000400 → 0,000368 | 0,027328 → 0,026945 |
| ≥5 | 0,012754 → **0,010639** | 0,019422 → **0,015598** |
| ≥10 | 0,006283 → 0,006040 | 0,012909 → 0,011224 |
| ≥25 | 0,000034 → 0,000041 | 0,011949 → 0,010363 |

**Observación favorable pero débil:** para T=5 a 30 días, el
modelo combinado de Q1 estatal + otra violencia Q1 clasifica entre
las 10 probabilidades mayores los **dos únicos positivos observados
de los 155 países a riesgo**: Kenya (Q1 estatal 3; 30d 12)
y Libya (Q1 estatal 3; 30d 5). El top10 incluye **8 negativos**,
y el modelo no ha elegido los casos de forma prospectiva.
A 90 días, el modelo combinado incluye **2 de 3 positivos**
dentro de los diez primeros (el tercero es South Africa,
Q1 estatal 0; 90d 6). La comparación con la climatología
muestra menor Brier en esta muestra, pero resulta
insuficiente para sostener un sistema de alertas validado.

La selección de un «mejor umbral» **después de mirar estas ocho
comparaciones** introduciría sesgo de selección. Incluso con
el diseño previo de la prueba, el equipo ya había investigado
resultados de 2026 para T=25. Estos resultados se presentan
**solo como exploración retrospectiva no ciega**, no como
una clasificación predictiva estable demostrada.

### Atribución de archivos adicionales y control de integridad

| Edición original UCDP Candidate | SHA-256 |
|---|---|
| `21.01.21.03` | `e14d274b78b52605d26e19c5e387ee4f7c98b398e4099bbe66d039757bc2970e` |
| `21.01.21.09` | `077b27b7b6490431bb040fb2c08739587d1a0a4fb6ff3ef3852ee5d8d8ef79c9` |
| `22.01.22.03` | `4111f9331f794e6bc20900af9c2ba63be3a7ac1ca97bfc231ee6129f97e83eb2` |
| `22.01.22.09` | `20d15637aa4b9ee80aed52a059d0552a8045867e493f103f6f8d7c117547b733` |

Los seis SHA-256 de 2024–2026 coinciden exactamente con el
[estudio 30/90 días anterior](../data/candidate-30-90-baseline-holdout.json).
El archivo de resultados informa asimismo los registros descartados
por precisión temporal y por fronteras de las ventanas. 
El `date_prec=0` no figura en el código oficial 1–5 y
permanece excluido; la fuente UCDP Candidate es provisional.

**Conclusión científica ajustada:** ampliar el horizonte a 90 días
produce más positivos, pero el problema estadístico de detectar
reactivaciones **sigue siendo grave** en todos los umbrales.
El modelo combinado merece una investigación prospectiva
de sensibilidad y estabilidad de los nuevos umbrales,
no una puesta en marcha de alertas con pretensión de fiabilidad.

## Conclusión permitida antes del cómputo

Este es un experimento de **suficiencia de eventos, intensidad del
indicador y señal de reactivación**. El mejor resultado de 2026 NO
identificará por sí mismo el mejor umbral para comercializar.
Un umbral bajo describe episodios menores y puede reflejar cobertura
o revisiones, no crisis estratégicas. Con 4 cohortes de entrenamiento
correlacionadas y 1 año de holdout no se demuestra generalización.
La validación real requiere emisión futura, latencia verificable,
comparador operativo y seguimiento de revisiones hasta GED anual.

**Privacidad:** solo fuentes públicas institucionales, nada de
identidades ni repositorios personales. Se preserva la atribución UCDP
Candidate. Sin publicación de eventos individuales ni fuentes de prensa.
