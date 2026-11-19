# Q-CANDIDATE · Estabilidad temporal de etiquetas y alertas de entrada (prerregistro)

**Diseño fijado: 19/11/2026, antes de calcular esta sensibilidad.** Estudio retrospectivo **exploratorio y no as-of certificado**. No crea ni emite predicciones. Las cuatro cohortes GEO2027, NEWCONF2027, ACD2027 y GEO2028 no cambian.

## Motivación y pregunta

Un Brier excelente en todo el conjunto puede estar dominado por países que ya registraban violencia. Este trabajo aísla países con **menos de 25 fallecidos de violencia estatal registrados de enero a marzo** en la edición Candidate Q1 de 2024, 2025 y 2026.

Dos preguntas independientes:
1. **¿Cuánto cambia la etiqueta de mayo (30 días) al pasar de Candidate Q2 a Candidate Q3, para un periodo objetivo idéntico?** Comparar enero-marzo del origen Q1 con registros de mayo presentes en la edición acumulada Q2 (enero–junio) y reobservados en la edición Q3 (enero–septiembre). Ambas etiquetas son **revisiones descriptivas** del mismo mes, no una verdad final.
2. **¿Hay evidencia robusta de discriminación de nuevos cruces en el holdout 2026 a 90 días?** Solo los países con Q1<25; el objetivo 90 días es el ya congelado en el benchmark original. Calcular falsos positivos/recall para K={5,10,20,50}; por existir grupos de **probabilidad idéntica**, reportar **mínimo, máximo y esperanza de aciertos bajo desempate uniforme**, además de cualquier ranking determinista. No atribuir habilidad al desempate alfabético o por `country_id`.

## Fuentes y reglas preexistentes (NO redefinidas)

- Nueve archivos originales oficiales: Q1/Q2/Q3 de 2024, 2025 y 2026. Recuperar SHA-256 y URL de los dos informes públicos congelados `candidate-30-90-baseline-holdout.json` y `candidate-q2-q3-vintage-revisions.json`. No sustituir retrospectivamente por la versión anual GED.
- Universo idéntico de **196 country_id** del registro GEO2027; no cambiar país ni probabilidades ya emitidas. En todos los archivos, para `type_of_violence=1`, `date_prec∈{1,2}`, solo eventos cuyo intervalo completo esté dentro de la ventana. `date_prec=0` o 3–5 quedan excluidos y contados. Sin rellenar ausencia como inexistencia de violencia real.
- Origen Q1: 1 enero–31 marzo. Mes evaluado: **1–30 mayo**, ambos incluidos. Etiqueta 1 si suma `best≥25`; etiqueta 0 significa solo que la **edición consultada no registra ese umbral**.
- Holdout original de 90 días: **1 mayo–29 julio**, con vector 2026 congelado, mismo entrenamiento exclusivamente 2024+2025, sin reentrenar ni seleccionar hiperparámetros. Se comprobará equivalencia exacta de origen y resultado Q3.
- Reportar para los tres años: conteo de países Q1<25, positivos Q2 frente a Q3, cruces arriba/abajo, IDs de eventos solo en una versión y cambios `best` entre eventos compartidos dentro de mayo, especialmente los países en riesgo de cruce. Congelar por año y agregado.
- Los K de alertas y los dos modelos comparados son predefinidos. Si la fracción de positivos es diminuta, evitar afirmaciones de capacidad predictiva, independencia entre 196 países o poder estadístico.

## Resultado observado: nueve archivos oficiales, replay íntegro

El informe [JSON agregado congelado](../data/candidate-onset-label-revision-ties.json)
se generó directamente de los nueve archivos UCDP Candidate
Q1/Q2/Q3 de 2024–2026, validados contra los SHA publicados previamente
en los dos estudios independientes. La misma etiqueta de mayo se calculó
sin cambios para ambos vintages Q2 y Q3. La CI reproducirá exactamente
las salidas o bloqueará la publicación.

| Año | Países Q1<25 | Cruces del umbral en mayo según Q2 | Según Q3 | Países con cambio de total `best` mayo | Cambios de etiqueta en los 196 |
|---|---:|---:|---:|---:|---:|
| 2024 | 170 | 0 | 0 | 16 | 0 |
| 2025 | 169 | 1 | 1 | 11 | 1 (fuera de Q1<25) |
| 2026 | 166 | 0 | 0 | 8 | 0 |
| **Total descriptivo** | **505** | **1** | **1** | **35 país-año** | **1** |

Aun cuando la etiqueta binaria del subconjunto en riesgo permanece estable
entre Q2 y Q3, **las muertes registradas sí cambian**. Las diferencias
absolutas entre totales nacionales en mayo suman 418 (2024), 287 (2025)
y 120 (2026), total **825**. La suma absoluta no representa víctimas
identificadas ni fallecimientos reales adicionales; solo revisiones del
recuento Candidate de un mismo mes. Además, en mayo hay IDs presentes
solo en una de las dos ediciones.

**Interpretación 30 días:** para este endpoint (≥25 muertes estatales
bien fechadas registradas en solo 30 días), apenas **1/505**
países-año inicialmente subumbral resulta positivo en las tres cohortes.
Ese dato es demasiado escaso para certificar sensibilidad, precisión o
calibración de un clasificador de nueva escalada a 30 días. Los 505 casos
son dependientes espacial y temporalmente, NO 505 observaciones IID.

## 2026 a 90 días: distinguir selección de grupo frente a ranking individual

En el holdout congelado de 2026 del PR #146 hay **166 países Q1<25**
y solamente **2 positivos** al comparar con la edición Candidate Q3:
**Kenia** (Q1=3; ventana de 90 días=29) e **Indonesia**
(Q1=13; ventana=27). Los dos pertenecen al grupo Q1
`best∈[1,24]` de **21 países**, al que el modelo de volumen
reciente asignó la misma probabilidad `0,1409826645`.
Los otros **145 países** tenían cero fallecidos registrados en Q1,
y ambos casos observados de 90 días proceden del grupo de 21.

El modelo distingue por tanto una **categoría de vigilancia de 21 países**,
no un orden individual fiable de esos 21. Si se eligen K países
arbitrariamente dentro de ese empate, las cotas son:

| Alertas entre los 166 subumbrales | Aciertos mínimo–máximo (modelo volumen) | Aciertos esperados con desempate uniforme |
|---|---:|---:|
| Top 5 | 0–2 | 0,476 |
| Top 10 | 0–2 | 0,952 |
| Top 20 | 1–2 | 1,905 |
| Top 50 | 2–2 | 2,000 |

En particular, el «1/10» encontrado con desempate por
`country_id` **no mide habilidad**: otro desempate de igual
probabilidad da 0/10 o 2/10. Los 21 países de la categoría
suponen 21/166=12,65 % del subconjunto, pero la inclusión
de ambos casos no basta para establecer validez futura ni ventaja
económica, dadas las revisiones, la selección histórica previa,
la dependencia geopolítica y un solo año de holdout. Si se convirtiera
esa categoría en alertas, implicaría **19 falsos positivos entre 21**
para el endpoint considerado en esta muestra. Tampoco se puede concluir
que haya ausencia real de violencia en los 145 restantes.

Los modelos de climatología global y persistencia binaria asignan
una única probabilidad compartida a los **166 países** del
subconjunto, por lo que carecen incluso de esta división en categorías.

**Conclusión del estudio:** la predicción de *continuidad* sigue
siendo razonablemente prometedora en retrospectiva. Para
*escaladas desde niveles bajos*, la evidencia de ranking
individual se reduce a una separación gruesa entre países
con y sin registros previos. No debe presentar un listado
ordenado de alertas como si estuviera respaldado por el modelo.

## Criterios y limitaciones

- No buscar un umbral alternativo que produzca mejores resultados de 2026: sería optimización a posteriori.
- Una edición posterior puede añadir o eliminar casos; Q3 NO es verdad final.
- La fecha real de primera publicación de Q1, Q2 y Q3 sigue sin estar acreditada individualmente. **No** declarar un backtest estrictamente `as-of` ni eficacia prospectiva por ese motivo.
- Para valorar utilidad operativa se requerirá **validación prospectiva** con fecha de emisión verificable, demora real de datos, umbral de pérdidas y costes de falsas alertas; este experimento mide estabilidad de etiquetas y fragilidad de rankings.
- El informe solo publicará agregados y códigos/etiquetas de países a alto nivel; no noticias, víctimas ni datos personales. Privacidad institucional IDEA LAB. Atribución UCDP Candidate con enlace <https://ucdp.uu.se/downloads/>.
