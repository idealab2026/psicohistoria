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


## Resultados exactos reproducidos (24-11-2026)

El programa ha combinado las matrices y los diez casos Candidate positivos de
los estudios fuente [2021/22](../data/candidate-ged-2021-22-resolution.json),
[2024/25](../data/candidate-to-annual-ged-resolution.json) y el [control
intra-GED 2024](../data/ged2024-annual-vintage-drift.json). Se verificaron
los 196 países de cada una de las cuatro cohortes y la identidad con
los **642 país-años** del indicador T=5/30d previamente congelado.

**Rectificación técnica de trazabilidad:** en el código del estudio #152,
la variable `previous` ya había sido convertida en diccionario al calcular
`source_prev_2024_25_sha256`, por lo que ese campo SHA-256 corresponde a
`json.dumps(previous, ensure_ascii=False, sort_keys=True).encode("utf8")`,
**no a los bytes literales del JSON en disco**. El nuevo control reproduce
**exactamente** esa huella histórica canónica (y además calcula hashes
independientes de los bytes de los tres informes actuales). La primera
ejecución rechazó erróneamente la comparación de SHA de distintas
representaciones; esto se corrigió sin cambiar las observaciones ni
relajar el cotejo del contenido fuente.

### Comparación anual exacta

| Año | Riesgo Q1 T=5 | Candidate Q3 positivos | Etiquetas que GED anual mantiene |
|---|---:|---:|---:|
| 2021 | 160 | 3 | 3 |
| 2022 | 161 | 1 | 1 |
| 2024 | 161 | 2 | 0 |
| 2025 | 160 | 4 | 1 |
| **Total** | **642** | **10** | **5** |

De los diez Candidate positivos se retienen **5/10** (IC binomial
exacto Clopper–Pearson 95 %: **18,7–81,3 %**). Para 2021–22 la retención
es **4/4** (IC 95 % **39,8–100 %**) y para 2024–25 es **1/6**
(IC 95 % **0,4–64,1 %**). El Fisher exacto bilateral de esa
partición es **0,04761905**, pero **no es confirmatorio**: se exploró
la división precisamente porque la anomalía ya se conocía.
Ni los intervalos binomiales IID son una medida completa de incertidumbre
entre países/conflictos dependientes.

### Casos, distancias y coding status del origen provisional

| Año | País | Candidate Q3 mayo `best` | GED anual mayo `best` | Muertes `Clear` Candidate | ¿Coincide al menos un ID del mismo país/ventana en GED? |
|---|---|---:|---:|---:|---|
| 2021 | Perú | 16 | 16 | 16 | Sí |
| 2021 | Turquía | 19 | 19 | 17 | Sí |
| 2021 | Israel | 247 | 252 | 247 | Sí |
| 2022 | Togo | 8 | 23 | 0 | Sí |
| 2024 | Brasil | 5 | 0 | 0 | No |
| 2024 | Bangladés | 5 | 0 | 5 | No |
| 2025 | Ecuador | 12 | 0 | 0 | No |
| 2025 | Brasil | 7 | 0 | 0 | No |
| 2025 | Libia | 7 | 0 | 0 | No |
| 2025 | Indonesia | 38 | 14 | 4 | Sí |

Los `0` de GED son **cero registros elegibles para este indicador
concreto**, no prueba de ausencia de violencia o de inexistencia de un evento.

### Contrastes exploratorios realizados, sin selección retrospectiva de reglas

| División entre los diez casos Candidate positivos | Retención grupo sí | Retención grupo no | Fisher bilateral exploratorio |
|---|---:|---:|---:|
| 2021–22 frente a 2024–25 | 4/4 | 1/6 | 0,0476 |
| Candidate `best≥10` frente a 5–9 | 4/5 | 1/5 | 0,2063 |
| `Clear best≥5` frente a inferior a 5 | 3/4 | 2/6 | 0,5238 |
| Algún `check dyad` frente a ninguno | 1/4 | 4/6 | 0,5238 |
| Al menos un ID idéntico en GED posterior frente a ninguno | 5/5 | 0/5 | 0,00794 |

**No interpretar la última fila como capacidad predictiva:** el supuesto
«predictor» se obtiene consultando **GED anual después del periodo objetivo**,
por lo que introduce **fuga temporal perfecta**. Se incluye únicamente para
mostrar que, en estos diez casos concretos, la recodificación/ausencia
de un identificador exacto acompaña a las etiquetas que cambian;
no distingue si el acontecimiento subyacente desapareció, cambió
de tipo, fue reasignado, fusionado o si se dividió.

**Distancia al umbral:** cinco casos Candidate tenían entre 5–9
fallecidos, de los cuales **uno** retiene la etiqueta (Togo);
otros cinco tenían ≥10, de los cuales retienen **cuatro**.
Hay composicionalidad entre las eras: en 2021/22 tres de cuatro
casos ya superaban diez, frente a dos de seis en 2024/25.
**No prueba que ese sea el mecanismo causal** de la heterogeneidad;
Ecuador (12) pierde la etiqueta e Indonesia (38) permanece,
y todo procede de una muestra seleccionada a posteriori.

**Estado `Clear`:** es insuficiente como garantía, porque Bangladés
2024 registraba 5 `Clear` y en GED25.1 no supera 5. Y
no es necesario, porque Togo 2022 (`check deaths`) e Indonesia 2025
(mayoría `check deaths`) sí se mantienen. Tampoco `check dyad`
demuestra falsedad: Indonesia contenía esa categoría y retiene
el indicador. Los registros son provisionales y GED usa criterios
anuales diferentes.

**Control intra-GED:** la edición GED26.1 posterior no altera ninguna
etiqueta T=5/30d del conjunto de riesgo 2024 respecto a GED25.1
(estudio #153). En 2024, la pérdida de las dos etiquetas se
produce en **Candidate→primer GED anual**, no al comparar
esas dos versiones anuales.

### Decisión posterior

No entrenar un **«modelo de confirmación GED»** con solo diez
positivos de cuatro cohortes dependientes, ni convertir
`best≥10` o `Clear` en filtros de alerta supuestamente
validados. Los resultados sugieren que la intensidad y la
distribución del coding status importan para diseñar
diagnósticos, pero **no explican causalmente** las diferencias
de política de inclusión por año.

La siguiente fase defendible requiere:

1. Construir más cohortes y **no seleccionar la versión GED de cierre**
   después de mirar las etiquetas; priorizar diseños con eventos
   y díadas de violencia, no solo clasificaciones de un país.
2. Separar el producto **Candidate provisional** del producto
   **GED anual consolidado** en todas las evaluaciones.
3. Conservar reglas de abstención para fuentes desactualizadas y
   certificar **primer momento de disponibilidad de los insumos**
   antes de emitir cualquier alerta prospectiva de 30/90 días.
4. Preservar los 620 pronósticos preemitidos de 2027/28, que son
   experimentos distintos y todavía no han sido resueltos.

Esta investigación no certifica habilidad predictiva ni emisión
prospectiva nueva.

**Salida íntegra reproducible:** [recuento de diez casos, IC exactos,
contrastes y hashes de los tres informes fuente](../data/candidate-ged-retention-strata.json).
