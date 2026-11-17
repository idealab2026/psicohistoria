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

## Resultados oficiales: el fallo de 2017 está relacionado con una revisión del estado de origen

Se han descargado y verificado por SHA-256 **siete ediciones GED**: 17.1 a 23.1. Las dos históricas añadidas son:
- GED 17.1 ZIP, 135.181 eventos, años 1989–2016, SHA-256 `6dcf0a3fa90c03295255d6f64540e679b034444eab1e00ec12462ac0e7e23baa`.
- GED 18.1 ZIP, 142.902 eventos, años 1989–2017, SHA-256 `9194d3c2849631e3b9dbcf1dd5842d3cfb35168491c071c7c74208be8106e882`.

El puente GED23.1→OrganizedViolenceCY23.1 continúa reproduciendo exactamente los 2.352 valores originales de 2011–2022 para los 196 GWNO. Todos los ZIP se comprueban antes de procesar resultados.

### El estado de Túnez no era estable al pasar de GED17 a GED18

| GED y cobertura máxima | Fallecidos estatales Túnez 2016 | Fallecidos Túnez 2017 | Resultado 2016→2017 |
|---|---:|---:|---|
| **17.1**, hasta 2016 | **0 registrados** | No disponible | **No evaluable** |
| **18.1**, hasta 2017 | **72** | **3** | **10: salida** |
| 19.1, hasta 2018 | 72 | 3 | 10: salida |
| 20.1, hasta 2019 | 72 | 3 | 10: salida |
| 21.1, hasta 2020 | 69 | 0 | 10: salida |
| 22.1, hasta 2021 | 88 | 15 | 10: salida |
| 23.1, hasta 2022 | 88 | 15 | 10: salida |

**Hallazgo decisivo:** la fuente GED17.1 de 2017, que termina en 2016, todavía **no registra** los eventos estatales tunecinos que GED18.1 atribuyó retrospectivamente a 2016 (72 muertes). GED17.1 no podía identificar como estado **alto** ese año bajo el umbral del proyecto, aunque la edición posterior reconstruya un estado alto en 2016. Por ello no existe el supuesto inicial 1 (alto) para construir una transición 10 usando *exclusivamente* GED17.1.

Las seis ediciones **GED18.1–23.1** coinciden en clasificar el trayecto como **10 (activo en 2016 → inactivo en 2017)**. Los recuentos cambian, pero no el estado binario. No equivale a afirmar que las verdaderas muertes fueron cero en GED17.1; fue **cero registrado en esa edición**.

GED17.1 se publicó en 2017 y GED18.1 después de 2017: **ninguna de las dos aporta un pronóstico original emitido con datos sellados en 2016**. Una edición posterior puede cambiar incluso el estado del año inicial, y no solo la etiqueta objetivo. Cualquier estudio que use retrospectivamente una edición posterior para generar una supuesta predicción del 2017 debe declararlo expresamente.

### ¿Qué probabilidad reconstruye hoy el Markov binario?

Para **comparar fuentes exclusivamente**, se ha reconstruido el Markov `Laplace=1, shrink=20` con los mismos 195 países (Siria queda excluida por cobertura antigua), con un soporte histórico común basado en **Country-Year23.1 de 2023** y entrenamientos truncados en el año objetivo de origen. No es la matriz de 196 países ni la fuente realmente disponible en 2016.

| Fuente GED | Estado Túnez 2016 | Probabilidad de salida en 2017, si inicialmente activo |
|---|---|---:|
| 17.1 | **Inactivo** | **No definida** |
| 18.1 | Activo | 18,26 % |
| 19.1 | Activo | 18,32 % |
| 20.1 | Activo | 17,97 % |
| 21.1 | Activo | 17,71 % |
| 22.1 | Activo | 15,33 % |
| 23.1 | Activo | 15,42 % |

La variación no se debe únicamente a Túnez: cambiar la edición afecta también los recuentos de transición del conjunto de países. El modelo considera más probable **la persistencia del estado activo**. Que se observara una salida con probabilidad entre 15–18 % **no prueba por sí solo un error de calibración ni un fallo de forecasting**; es un evento relativamente poco probable que puede ocurrir. No se han publicado pruebas prospectivas originales para ese origen.

En un contrafactual puramente matemático, sustituir exclusivamente en GED22.1 las etiquetas históricas de Túnez de 2013–2015 por las de GED21.1 aumenta la probabilidad de salida de 2017 de **15,33 % a 17,69 %**; efecto de revisión GED22.1−contrafactual **−2,3653 puntos porcentuales**, manteniendo los demás datos fijos. Es una **base híbrida que nunca fue publicada por UCDP**, no una prueba causal.

### El origen 2014 también cambia de estado entre versiones

La otra pregunta era *primera salida exactamente en 2017 desde 2014*. Para que esta probabilidad esté definida como **primera salida de un estado activo**, **2014 debe comenzar activo**:

- **GED17.1–GED21.1:** Túnez figura como **inactivo en 2014**, con cero fallecidos estatales registrados. El evento condicional *primera salida desde activo en 2014* **no está definido**.
- **GED22.1–GED23.1:** 2014 cambia retroactivamente a **51 fallecidos**, estado activo. Entonces la reconstrucción Markov 195-GWNO atribuye al **primer abandono exactamente en 2017** un **11,89 %–11,93 %**, y a **haber abandonado al menos una vez hasta 2017**, un **43,74 %–43,95 %**.

Son preguntas distintas: **probabilidad exacta de salida en 2017**, **probabilidad acumulada de salida antes de cerrar 2017** y **probabilidad de salida condicional al estado activo en 2016**. Comparar sus porcentajes sin distinguir la definición es un error metodológico.

**Conclusión científica:** la hipótesis de que el modelo `no acertó` la salida de Túnez en 2017 no puede evaluarse limpiamente como forecasting auténticamente prospectivo con estas fuentes. La propia condición inicial de 2016 no aparece como activa hasta una edición publicada después. El análisis previo de 2024 tampoco responde al episodio de 2017. La nueva evidencia documenta **revisión de la fuente y definición del suceso**, no capacidad predictiva ex ante.

## Prohibiciones y evaluación

- No reutilizar un valor del estudio retrospectivo de **2024** para justificar un supuesto fallo de **2017**.
- No atribuir causalidad a una modificación de la fuente ni confundir una salida poco probable con una prueba de mala calibración de un sistema probabilístico.
- No afirmar que los modelos públicos con 195 países sean equivalentes a un cálculo anterior cuyo artefacto exacto de entrenamiento no se ha certificado en IDEA LAB.
- No alterar las predicciones ni el SHA de GEO2027 o GEO2028, no inventar desenlaces 2027–2028, no reconstruir una firma temporal inexistente.

El informe determinista `data/geo-tunisia-original-2017-exit-vintage-diagnostic.json` se reproduce desde archivos oficiales en `scripts/audit_geo_tunisia_original_2017_exit_vintages.py`. Tests en `scripts/test_audit_geo_tunisia_original_2017_exit_vintages.py`; auditoría de privacidad y control de despliegue institucional obligatorios.
