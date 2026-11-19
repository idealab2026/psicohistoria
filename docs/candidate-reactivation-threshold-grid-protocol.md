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
