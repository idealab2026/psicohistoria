# PSICOHISTORIA · Heterogeneidad de la retención Candidate→GED anual (24-11-2026)

**Exploración explicativa POSTERIOR a observar la discrepancia 2021–2022 vs 2024–2025.** Las particiones NO son un prerregistro ciego ni una validación independiente. Su único propósito es distinguir mecanismos compatibles con los diez casos conocidos, detectar contradicciones y preparar un diseño prospectivo posterior. No se reajusta modelo ni se usa 2026 para entrenar.

## Datos congelados y pregunta

Dos informes institucionales previamente computados desde originales UCDP SHA-pinned:
- `data/candidate-ged-2021-22-resolution.json` (GED22.1/23.1, Candidate Q1/Q3 2021–2022, PR #152).
- `data/candidate-to-annual-ged-resolution.json` (GED25.1/26.1, Candidate Q1/Q2/Q3 2024–2025, PR #151).
- Como control adicional, `data/ged2024-annual-vintage-drift.json` (2024 GED25.1→26.1, PR #153): confirmar que el corte posterior no altera el indicador T=5/30d.

Se mantendrá el universo fijo de 196 códigos de país y el **mismo endpoint** de informes previos: país cuyo Candidate Q1 del año registra menos de 5 muertes `best` de violencia estatal (tipo1, precisión 1/2, eventos completamente dentro de enero–marzo) y cuyo Candidate Q3 registra al menos 5 de esas muertes en **1–30 mayo**. No reinterpretar esos registros como nacimiento real de una guerra. GED anual usa la primera edición disponible para esa anualidad.

Los diez casos positivos Candidate Q3 (4 de 2021–22 y 6 de 2024–25) se extraerán de los informes congelados, preservando `country_id/year`, total Candidate, total GED, `code_status` y nº de coincidencias exactas de ID con GED. Confirmar que los totales `code_status` suman exactamente el `best` de Candidate; bloquear ante cualquier diferencia, duplicado, ingreso fuera del universo o inconsistencia con los 196 vectores publicados. Los países con solo Q2 positivo no se incluirán.

## Contrastes DESCRIPTIVOS predefinidos para esta fase (hipótesis exploratorias postselección)

1. **Era:** 2021–22 vs 2024–25, positivos Candidate que conservan la etiqueta en GED anual. Proporciones con IC binomial exacto Clopper–Pearson 95 %; Fisher exacto bilateral con márgenes fijos. Dado que los bloques temporales se escogieron porque ya se observaron muy distintos, el valor p NO tiene carácter confirmatorio ni causal.
2. **Distancia al umbral:** total `best` Candidate 5–9 vs ≥10. Es un corte heurístico razonable pero inspeccionado a posteriori, no un parámetro calibrado. Calcular asociación y matriz por era. No convertirla en regla de alerta.
3. **Calidad de codificación:** al menos 5 fallecidos Candidate clasificados `Clear` (sí/no); existencia de algún `check dyad` (sí/no). Comparar etiquetas conservadas y perdidas. `Clear` es una etiqueta provisional de codificación, no validación final; otros estados no significan falsedad.
4. **Correspondencia exacta de identificadores:** al menos un evento Candidate de mayo compartido con GED anual bajo mismo país/ventana; contar junto a la retención por país. Esta variable **usa GED anual posterior y por tanto constituye leakage**. Nunca usarla como predictor operativo de alertas ni atribuirle causalidad. Su finalidad es diagnosticar *cómo* difieren los informes.
5. **Separación de escalas:** mostrar una confusión del indicador entre los **642 países-año a riesgo** y, de forma separada, las tablas condicionadas a los diez positivos Candidate. No confundir concordancia de casos con tasa general de desaparición de acontecimientos. Un GED=0 bajo estas reglas no prueba que no hubiera hechos violentos.
6. **Estabilidad intra-GED:** el PR #153 verificó 2024 con ediciones GED25.1 y GED26.1. El control debe bloquear si el resumen de T=5/30 cambia, sin recalcular fuentes.

Los diez casos y las cuatro cohortes **no son observaciones independientes**: países repetidos, conflictos compartidos, cambios de cobertura y selección por un umbral. Reportar n exactos, proporciones y categorías; ningún clasificador será entrenado, validado o recomendado sobre esos diez ejemplos. No extrapolar la diferencia temporal a un supuesto cambio metodológico documentado de UCDP sin pruebas adicionales.

## Política científica y privacidad

- Datos públicos agregados por país de informes institucionales ya verificados; no re-descargar originales, no fichas de personas ni noticias.
- Pruebas sintéticas adversariales de doble conteo, fuente/ventana mal cruzada, discrepancia de estados y falsa inferencia por coincidencia de ID.
- Congelar salida JSON; CI exige reproducción idéntica y auditoría de lista institucional.
- No tocar predicciones emitidas de GEO2027, NEWCONF2027, ACD2027 y GEO2028 (620 preguntas congeladas).
- No hablar de precisión prospectiva, confianza en alertas reales o probabilidad personal de que una muerte «ocurrió»; las comparaciones son entre **ediciones de base de datos**, no verdad ontológica.
- Preparar a partir de los hallazgos una **regla de presentación**: identificar claramente endpoint Candidate provisional frente a GED anual consolidado y abstenerse de afirmar onset validado hasta contar con un origen temporal certificable y pruebas independientes fuera de muestra.
