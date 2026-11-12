# GEO-2027 — Segunda emisión prospectiva de calibración *shadow*

**Fecha de preparación: 12 de noviembre de 2026.** La emisión efectiva se acredita exclusivamente con el primer commit público del archivo canónico completo, **no** con esta documentación, la generación de un fichero ni el reloj del desarrollador.

## Qué es y qué no es

Una **segunda cohorte prospectiva diferenciada**, de 196 probabilidades para 2027, calculada a partir de:

- Las **196 probabilidades originales GEO-2027**, SHA-256 `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`, primer commit `3bb3561c8d6182c30624591276c705fb76ce99dc`, 10/11/2026.
- El experimento histórico `data/geo2027-temporal-calibration-ablation.json`, cuyos dos interceptos se estimaron **solo** en datos históricos objetivos 2012–2019. La receta fue diseñada después de haber observado los problemas de calibración y los resultados históricos 2024–2025, por lo que la elección del modelo es **post hoc**.
- La misma edición original UCDP OrganizedViolenceCY 26.1 con datos observados hasta 2025, **sin añadir información de 2026 ni 2027**.

**No se sustituye, recalibra ni modifica** el compromiso original GEO-2027, las 15 alertas emitidas, NEWCONF-2027, sus hashes, primeras fechas de emisión, ni sus métricas primarias. Se publica otro archivo y otro manifiesto: la identidad del predictor shadow termina en `CALIBRATED-SHADOW-V1`.

## Fórmula congelada

Para cada país con estado de origen `s∈{0,1}`, partiendo de su probabilidad emitida original de estar activo en 2027 `p`, definimos `q=p` si `s=0` (entrada) y `q=1−p` si `s=1` (resolución de umbral). Se aplica:

\[
q_{shadow}=\mathrm{logit}^{-1}(\mathrm{logit}(q)+\alpha_s)
\]

Con `α_0 = −0.2921540997775962` y `α_1 = −0.7367471232834963`, estimados en **2012–2019**, equivalentes a multiplicadores de *odds* 0,746653 y 0,478668, respectivamente.

La salida `p_shadow_active_2027=q_shadow` para `s=0` y `1−q_shadow` para `s=1`. El redondeo publicado es de **12 decimales**. Esta transformación es estrictamente monótona dentro de cada estado de origen; no cambia la ordenación de países ni la identidad de ninguna de las 15 alertas.

**Señal de advertencia:** este ajuste fue elegido tras explorar resultados históricos en los que parecía funcionar. Su evaluación en 2027 será prospectiva respecto al *resultado futuro*, pero no confirmatoria respecto a la *selección del método*. Cualquier declaración pública de acierto debe reconocer esta distinción.

## Contrato de evaluación de 2027, fijado ahora

El objetivo será el indicador país-año de violencia organizada **estatal** definido como 25 o más muertes en 2027 según la **primera edición oficial UCDP completa** que cubra ese año. No significa aparición de una nueva guerra, desaparición política de un conflicto ni episodios `newconf`.

1. Se exige **cobertura completa de los mismos 196 códigos de país**. Ninguna ausencia se imputará como cero. Mientras falte alguna etiqueta, no se emite un Brier definitivo ni un resultado de éxito.
2. **Métrica primaria del shadow:** diferencia emparejada de Brier `Brier_shadow − Brier_GEO2027_original` en los 196 países del mismo corte temporal, con el modelo emitido original como comparador fijo. Una diferencia negativa favorecerá al shadow.
3. **Métrica secundaria:** diferencia de log-loss `shadow − original`; se publicarán también Brier y log-loss por estado inicial 2025 y frente al Markov global original.
4. La evidencia de incertidumbre debe reconocer correlaciones geográficas y posibles shocks comunes entre países; no se pueden tratar automáticamente los 196 países como observaciones independientes ni elegir intervalos a posteriori para obtener significación.
5. El ajuste de dos interceptos ya fue seleccionado tras examinar una cohorte histórica posterior. No se podrán anunciar sus resultados como confirmación independiente de la selección del modelo, ni sustituir el modelo primario por este si conviene para mostrar un acierto retrospectivo.
6. La auditoría futura certificará por separado fecha, edición, integridad del ZIP oficial, correspondencia de países y revisión posterior. Una URL declarada por un operador **no prueba** la primera publicación.

**Estado actual:** datos de 2027 observados: **cero**. No se atribuye ninguna capacidad predictiva demostrada. Ninguna rutina de resolución futura escribe resultados mientras la fuente original oficial no esté disponible y verificada.

## Cadena de integridad

`scripts/prepare_geo2027_calibrated_shadow.py` rechaza cambios en la predicción original, en el manifiesto inicial, en los 2 interceptos históricos, en la separación temporal, en la definición de objetivo, en la primera emisión de alertas o en la lista de países. Su salida canónica ordenada se publicará con un SHA-256 propio; un manifiesto posterior registrará el commit público **exacto** en el que aparecieron por primera vez sus 196 probabilidades.

La auditoría automatizada debe reconstruir el candidato byte a byte desde esos archivos inmutables y rechazar modificaciones posteriores, incluidas modificaciones silenciosas del generador. No se publica ninguna referencia a repositorios ni cuentas personales.
