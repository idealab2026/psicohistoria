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

## Criterios y limitaciones

- No buscar un umbral alternativo que produzca mejores resultados de 2026: sería optimización a posteriori.
- Una edición posterior puede añadir o eliminar casos; Q3 NO es verdad final.
- La fecha real de primera publicación de Q1, Q2 y Q3 sigue sin estar acreditada individualmente. **No** declarar un backtest estrictamente `as-of` ni eficacia prospectiva por ese motivo.
- Para valorar utilidad operativa se requerirá **validación prospectiva** con fecha de emisión verificable, demora real de datos, umbral de pérdidas y costes de falsas alertas; este experimento mide estabilidad de etiquetas y fragilidad de rankings.
- El informe solo publicará agregados y códigos/etiquetas de países a alto nivel; no noticias, víctimas ni datos personales. Privacidad institucional IDEA LAB. Atribución UCDP Candidate con enlace <https://ucdp.uu.se/downloads/>.
