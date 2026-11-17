# PSICOHISTORIA · Túnez: qué ocurrió con la salida observada en 2017

**Protocolo preespecificado el 17/11/2026 antes de obtener el nuevo resultado oficial. No es un nuevo pronóstico.**

## Identificación exacta del problema

La pregunta histórica de octubre no se refería a Túnez en 2024, analizado en la [PR #112](geo-ged-tunisia-h2-attribution.md). Se refería a una **transición binaria de violencia estatal**: si en **2016** había 25 o más fallecidos estatales y en **2017** ya no, el estado era **10** (*salida de violencia alta*). Separadamente se había considerado el suceso **primera salida exactamente en 2017** desde un origen anterior **2014**.

Los dos sucesos no deben mezclarse. El primero es un paso anual 2016→2017. El segundo es un tiempo de primer cruce condicionado al estado inicial de 2014. La fórmula `q11²×(1−q11)` describe una primera salida a tres años **solo** si la fuente etiqueta 2014 como activo; `1−q11³` expresa cualquier salida acumulada hasta ese horizonte bajo la misma condición, no la probabilidad del año exacto. Estos cálculos son **una nueva reconstrucción pública bajo Markov homogéneo**, no la reedición del antiguo estudio.

## Fuentes que se confrontan

[Archivo oficial histórico UCDP GED](https://ucdp.uu.se/downloads/olddw.html): GED **17.1** (serie hasta **2016**), **18.1** (hasta **2017**), 19.1 (2018), 20.1 (2019), 21.1 (2020), 22.1 (2021), 23.1 (2022). Recuperar los ZIP oficiales, fijar sus huellas SHA-256 y verificar las columnas originales de eventos: `id`, `year`, `country_id`, `type_of_violence`, `best`. El indicador es la suma de `best` para **tipo 1** (violencia estatal), agrupada por GWNO×año. Se verifica el puente exacto ya certificado GED23.1→OrganizedViolenceCY23.1 de 2.352 país-años, 2011–2022.

**Cronología:** UCDP [anunció la GED17.1 en 2017](https://ucdp.uu.se/downloads/updatealert/ucdp_updatealert26.html); esa versión contiene el resultado de **2016**, pero no estaba publicada en el origen **2016**. GED18.1, que incluye el objetivo **2017**, se difundió después de ese año. Esto impide considerar una reconstrucción de la edición 17.1 desde 2016 como una predicción registrada genuinamente antes del desenlace. Un SHA actual no prueba la disponibilidad del archivo ese día.

## Tres objetivos científicos separados

1. **Verificación del resultado.** Contrastar las etiquetas 2016 y 2017 para Túnez en GED18.1–23.1 y documentar si se mantiene o cambia el episodio **10** bajo revisiones posteriores.
2. **Análisis de cambios históricos en los datos.** Publicar cifras de Túnez de 2013–2018 por edición, con especial atención al cambio GED21.1→22.1 que transformó **2013, 2014 y 2015**: `(0,0,17)→(29,51,75)`.
3. **Sensibilidad del modelo, no réplicas de predicciones antiguas.** Mantener fijos Laplace=1 y contracción global=20, truncar los historiales a cada origen, estimar las tasas locales y globales de transición, y mostrar dos probabilidades diferenciadas: `P(1→0 en 2017 | activo en 2016)` y `P(primera salida exactamente en 2017 | activo en 2014)`. La segunda se presenta como **no definida** si la edición etiqueta **2014** como inactivo.

## Control de cobertura que no debe ocultarse

La serie GED **17.1, 18.1 y 19.1 excluía Siria**, incorporada por primera vez a GED20.1 según el [aviso oficial UCDP 2020](https://ucdp.uu.se/downloads/updatealert/ucdp_updatealert34.html). Para una comparación de entrenamiento con todas las ediciones se utiliza una cohorte de **195 GWNO** (los 196 originales menos Siria). Siria **no se imputa como un país en paz**. Esto tampoco es una predicción original de los 196 países.

Para evitar crear exposiciones ficticias en países inexistentes en años antiguos, el algoritmo utiliza **solo los país-años existentes en OrganizedViolenceCY23.1** como máscara homogénea de soporte, y rellena cero exclusivamente cuando la edición GED no registra un evento estatal en ese país-año. **Esa máscara procede de 2023 y tampoco era conocida en 2014/2016**; cualquier probabilidad resultante es un experimento retrospectivo, no un resultado contemporáneo.

En los dos modelos el indicador binario sigue siendo `best ≥25`. Se contrasta asimismo un conjunto híbrido exclusivamente ilustrativo: GED22.1 con los valores de Túnez 2013–2015 sustituidos por GED21.1. El cálculo permite medir cuánto afecta esa revisión, pero **esa base híbrida nunca existió como edición oficial de UCDP**.

## Prohibiciones y evaluación

- No reutilizar un valor del estudio retrospectivo de **2024** para justificar un supuesto fallo de **2017**.
- No atribuir causalidad a una modificación de la fuente ni confundir una salida poco probable con una prueba de mala calibración de un sistema probabilístico.
- No afirmar que los modelos públicos con 195 países sean equivalentes a un cálculo anterior cuyo artefacto exacto de entrenamiento no se ha certificado en IDEA LAB.
- No alterar las predicciones ni el SHA de GEO2027 o GEO2028, no inventar desenlaces 2027–2028, no reconstruir una firma temporal inexistente.

El informe determinista `data/geo-tunisia-original-2017-exit-vintage-diagnostic.json` se reproduce desde archivos oficiales en `scripts/audit_geo_tunisia_original_2017_exit_vintages.py`. Tests en `scripts/test_audit_geo_tunisia_original_2017_exit_vintages.py`; auditoría de privacidad y control de despliegue institucional obligatorios.
