# PSICOHISTORIA · IDEA LAB

Laboratorio público de investigación de sistemas complejos, fenómenos colectivos y evaluación de pronósticos.

**Estado actual: versión pública experimental, reconstruida de forma independiente.** El sitio incluye diez vistas navegables con formato oscuro, mapa de investigación, explorador de escenarios, evaluación probabilística, registro y hoja de ruta, y herramientas locales de preparación de hipótesis y guiones.

## GEO-2027 · Persistencia frente a nuevos cruces de umbral (10-11-2026)

**La mejora agregada no responde necesariamente a predecir nuevas guerras.** Hemos descompuesto las 392 observaciones históricas de ediciones UCDP distintas según el estado del país al final del año de origen, utilizando **exactamente el modelo Markov emitido para 2027**, sin modificar las probabilidades públicas.

| Estado en el año de origen | Países-año | Resultados positivos en el año evaluado | Brier modelo | Brier Markov global | Brier Skill |
|---|---:|---:|---:|---:|---:|
| Ya superaban 25 muertes `state-based` | **71** | **61** | 0,11892 | 0,14508 | **+18,03 %** |
| Estaban por debajo del umbral | **321** | **8** | 0,02265 | 0,02521 | **+10,17 %** |

**61 de 69 positivos (88,41 %) corresponden a persistencia de una situación ya por encima del umbral.** Solo ocho positivos partían de un estado anterior por debajo de 25. El intervalo de bootstrap agrupado por país para la diferencia Brier (modelo menos Markov global) en el estrato inicialmente inferior a 25 es **[−0,00740, +0,00068]**, **incluye cero**; no acredita una mejora sólida para nuevos cruces del umbral. Para países ya por encima del umbral el intervalo exploratorio es **[−0,03965, −0,01220]**. Dos años objetivo no permiten modelar adecuadamente choques compartidos entre países.

Por año, 2024 registra 4 entradas al estado positivo y 31 persistencias, frente a 2025 con otras 4 entradas y 30 persistencias. La precisión retrospectiva top-10 (10/10 en 2024 y 9/10 en 2025) está dominada por continuidad de conflictos violentos existentes, **no demuestra detección del inicio de nuevas guerras**. La variable es *muertes por violencia organizada con participación estatal*, no el indicador UCDP `onset2`.

**Otra restricción temporal:** el horizonte Markov es de **dos pasos entre años de datos** (2022→2024; 2023→2025); las ediciones que contienen el estado del año de origen solo se publican después del cierre de ese año. Por tanto, no cabe afirmar que esos resultados habrían estado disponibles con **dos años completos de preaviso operativo**. Las fechas de publicación originales carecen de notarización independiente y el experimento se reconstruyó en 2026.

El estudio se ejecuta con los cuatro archivos UCDP protegidos por hash y se publica en `data/forecast-2027-origin-state-diagnostic.json`; código `scripts/diagnose_2027_origin_state.py`, tests adversariales y control obligatorio `origin_state_diagnostic` antes de despliegue. **No se han emitido nuevas predicciones ni evaluado resultados de 2027.** La cohorte prospectiva original de 196 países conserva sus probabilidades y su SHA-256.

## GEO-2027 · Contraste histórico entre ediciones oficiales realmente distintas (10-11-2026)

**Resultado nuevo:** investigación con la misma ecuación probabilística, horizonte de dos años y referencias previamente congelados para GEO-2027, pero esta vez los años de entrenamiento proceden de una edición UCDP previa **diferente** de la utilizada para observar cada desenlace. No se reconstruye el pasado únicamente con una misma edición revisada.

| Ficheros de origen → resultado | Corte de entrenamiento | Año observado | Países | Umbral superado |
|---|---:|---:|---:|---:|
| OrganizedViolenceCY **23.1 → 25.1** | 2022 | 2024 | 196 | 35 |
| OrganizedViolenceCY **24.1 → 26.1** | 2023 | 2025 | 196 | 34 |
| **Total** | | | **392** | **69** |

La versión 23.1 original existe como **Excel XLSX**, mientras 24.1/25.1/26.1 se descargan en CSV comprimido; se procesan por separado con validación estricta de la unidad país-año y las columnas oficiales `country_id_cy`, `year_cy`, `sb_total_deaths_best_cy` (alias sin sufijo en 26.1). El motor verifica SHA-256 **antes** de cargar cada archivo, prohíbe cualquier observación posterior al corte dentro del entrenamiento y solo añade el resultado del año objetivo a la evaluación.

| Modelo | Brier ↓ | Log-loss ↓ |
|---|---:|---:|
| Markov por país, prior 20 | **0,04008406** | **0,15439774** |
| Markov global | 0,04692112 | 0,19006909 |
| Frecuencia global últimos cinco años | 0,14506787 | 0,46541257 |

Mejora retrospectiva en Brier: **14,57 % frente a Markov global** y **72,37 % frente a frecuencia global**. La calibración descriptiva por siete bandas presenta un error absoluto agrupado de **3,46 puntos porcentuales**; algunas bandas tienen muy pocos casos y no permiten inferencia prospectiva. El bootstrap exploratorio agrupado en país (2000 réplicas) arroja una diferencia modelo menos Markov global entre **−0,01133 y −0,00287**. No captura adecuadamente los choques compartidos ni el escaso número de años objetivo.

La revisión histórica de etiquetas binarias aporta un control empírico: **6 cambios** entre las ediciones 23.1→25.1 en 6544 países-año comunes hasta 2022; **7 cambios** entre 24.1→26.1 en 6740 registros hasta 2023. El entrenamiento se basa estrictamente en la versión antigua, sin utilizar esas revisiones posteriores.

**Ficheros fuente oficiales y sus huellas**: 23.1 XLSX `6c7dc09cc3173b21568a88d70862bee6a9199b2c6b217719698d9298ca8ecaff`; 24.1 ZIP `00410bdb65023d1bc8799f47f188677965046bb73447ee33094782db30076260`; 25.1 ZIP `564ce9a33652a5d7adef30f00ce6ac86411dedbcc10ef60ca9bdfbfeb9fea917`; 26.1 ZIP `66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`. Los enlaces se descubrieron en el [archivo histórico oficial](https://ucdp.uu.se/downloads/olddw.html), no se infirieron.

**Límite irrenunciable:** el estudio se ha ejecutado **ex post en 2026**. Aunque la estructura y el contenido de las ediciones archivadas se verifican, **las fechas originales no tienen un sellado independiente y no se emitió realmente ninguna predicción en 2023–2024**. El nuevo contraste es mejor evidencia histórica que la prueba de vintage revisada, pero todavía no equivale a la validación prospectiva de 2027.

Resultados reproducibles en `data/forecast-2027-archival-cross-release.json`; código `scripts/backtest_archived_country_vintages.py` y pruebas `scripts/test_backtest_archived_country_vintages.py`. GitHub Actions recalcula el resultado desde los cuatro archivos oficiales con hash fijado y bloquea el despliegue si cambia. **Las 196 probabilidades de 2027, su SHA y su protocolo no cambian; cero resultados de 2027 evaluados.**

## GEO-2027 · Backtest retrospectivo del modelo emitido (10-11-2026)

Se ha evaluado **exactamente el modelo y los baselines fijados para GEO-2027**, sin alterar el JSON de 196 pronósticos ni sus parámetros: Markov por país con prior 20, Laplace 1 y horizonte de dos años; referencias Markov global y frecuencia global de los cinco años anteriores al origen.

El motor `scripts/backtest_statebased_2027_spec.py` genera un *rolling-origin* de **14 años objetivo, 2012–2025**, fijando el entrenamiento en cada año objetivo menos dos. La fuente es la única edición oficial UCDP OrganizedViolenceCY 26.1 (SHA-256 **`66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34`**), por lo que su **historial está revisado retrospectivamente en 2026**: no es un estudio *point-in-time* verificado ni evidencia de predicciones emitidas antes de cada año.

| Modelo | Brier (menor es mejor) | Log-loss (menor es mejor) |
|---|---:|---:|
| Markov por país (idéntica fórmula a GEO-2027) | **0,04502180** | **0,17294718** |
| Markov global | 0,05151912 | 0,20554572 |
| Frecuencia global de los últimos cinco años | 0,13828517 | 0,44938370 |

Resultados: **2.742** observaciones país-año, **454** observaciones que superaron el umbral de 25 fallecimientos; **12,61 %** de reducción relativa de Brier respecto al Markov global y **67,44 %** respecto a la frecuencia global. El contraste por bootstrap agrupado en país (2.000 réplicas) da un intervalo exploratorio para la diferencia Brier modelo menos Markov global de **[−0,00932, −0,00379]**. La agrupación por país no captura choques comunes entre países ni toda la dependencia derivada de horizontes solapados; no se utiliza para reclamar significación confirmatoria. El error absoluto de calibración por los grupos fijados es aproximadamente **3,20 pp** (modelo) y **4,81 pp** (Markov global), dependiente de los intervalos de agrupación.

El estudio completo incluye los 14 años individuales, intervalos, probabilidades medias frente a tasas observadas, ausencia de etiquetas interpretadas como cero y pruebas contra fuga de información posterior al origen. Archivo agregado `data/forecast-2027-historical-backtest.json`, resumen en `data/research.json`, tests en `scripts/test_backtest_statebased_2027_spec.py`. **No hay datos de resultado de 2027 y no se modifican las 196 predicciones publicadas**. La evaluación verdaderamente prospectiva sigue pendiente de la primera edición oficial completa posterior a 2027.

## GEO-2027 · Auditoría independiente de reproducibilidad (10-11-2026)

Un segundo cálculo independiente ha reconstruido **las 196 probabilidades originales** utilizando únicamente el ZIP oficial **UCDP OrganizedViolenceCY 26.1** con SHA-256 fijo. El job ejecuta dos comprobaciones complementarias: (i) regenera el fichero de emisión **byte por byte** con el código preregistrado, y (ii) implementa las ecuaciones Markov de forma separada y compara cada probabilidad por país con la ya publicada. El fichero original no se reescribe.

Resultados agregados registrados en `data/forecast-2027-audit.json`: 34 países superaban el umbral en 2025; para 2027 la suma de probabilidades del modelo es **33,6254** países y la suma de la referencia global es **34,5295**. Existen 73 valores de probabilidad diferentes entre 196 países; 112 están por debajo del 5 % y 34 por encima del 50 %. Se trata de **distribuciones previstas, no resultados futuros observados**. Ningún pronóstico ha sido evaluado ni se reclama superioridad del modelo.

La auditoría se ejecuta en CI con `scripts/audit_frozen_2027.py --check-report data/forecast-2027-audit.json` y se convierte en una puerta obligatoria del despliegue público. Pruebas adversariales en `scripts/test_audit_frozen_2027.py` rechazan cambios en probabilidades, huellas, manifiesto o información posterior al corte de 2025. El conjunto de predicciones emitidas sigue siendo idéntico al registrado antes de 2027.

## GEO-2027 · Primera cohorte prospectiva pública emitida

Se ha añadido un protocolo científico para elaborar **antes de 2027** una primera cohorte prospectiva de **196 países**, prediciendo si en 2027 se registrarán **25 o más muertes anuales por violencia organizada de base estatal** en el campo `sb_total_deaths_best` del UCDP OrganizedViolenceCY. **No equivale a UCDP Onset `onset2`** ni a violencia gubernamental contra civiles: es una nueva pregunta científica y un horizonte fijo de dos años desde 2025.

Fuente de entrada: UCDP OrganizedViolenceCY 26.1, con datos hasta 2025 y SHA-256 publicado. Se congela una estimación Markov a dos pasos por país regularizada (prior 20), la tasa global de los últimos cinco años como referencia principal, el comparador Markov global, Brier como pérdida primaria y un criterio de resolución futura que impide convertir países ausentes en negativos.

**Estado actual:** primera cohorte de 196 probabilidades **emitida públicamente el 10 de noviembre de 2026 a las 17:23:12 UTC**, antes de comenzar 2027. La metodología estaba congelada en `main` desde las 17:20:43 UTC. La primera publicación íntegra corresponde al commit institucional `3bb3561c8d6182c30624591276c705fb76ce99dc`. SHA-256 inmutable del fichero `data/forecast-2027-ucdp261.json`: `5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5`. El commit `8b924e0b0c7a07e27977160c9658cfed77940aff` (17:32:54 UTC) preserva por primera vez el fichero **byte a byte idéntico** al producido por el generador, incluido el salto de línea final; el commit anterior `3bb3561c` ya publicaba las 196 probabilidades, pero sin ese terminador de archivo. Ambas publicaciones preceden a 2027. El manifiesto `data/forecast-2027-manifest.json` registra origen, estatus y corte. **No hay resultados oficiales observados de 2027, calibración demostrada ni evaluación prospectiva completada.** El commit de GitHub es un compromiso público verificable por hashes, pero **no** un sello de tiempo criptográfico de autoridad independiente.

Protocolo completo: `docs/forecast-2027-protocol.md`. Código y pruebas: `scripts/forecast_2027_statebased.py` y `scripts/test_forecast_2027_statebased.py`.

### Preparación de evaluación futura de GEO-2027

`scripts/evaluate_2027_official.py` proporciona un evaluador **offline, sin acceso a nuevos datos hasta su aportación explícita**. Exige los bytes íntegros y SHA-256 de la cohorte original, manifiesto de emisión, un ZIP oficial nuevo con etiquetas de 2027, URL y SHA-256 proporcionados para esa edición y una fecha de publicación posterior al cierre de 2027. Rechaza duplicados país-año, esquemas incompatibles y fuentes sin observaciones de 2027. No trata países ausentes como 0, reporta denominadores y bloquea puntuaciones si se resuelve menos del **95 %** de los 196 países.

Cuando exista una fuente futura, calculará Brier, log-loss, comparación contra ambas referencias congeladas y bootstrap de 2.000 repeticiones, sin entrenar de nuevo ni modificar probabilidades. El resultado queda etiquetado **SELF_REPORTED_OFFICIAL_SOURCE_NEEDS_FIRST_RELEASE_ATTESTATION** hasta comprobar externamente la fecha y el carácter de *primera edición* oficial. Este software **no implica que hayan aparecido resultados de 2027**: los ejemplos en `scripts/test_evaluate_2027_official.py` son sintéticos.

## Navegación

| Grupo | Vistas | Función pública |
| --- | --- | --- |
| Inicio | Resumen | Estado, líneas científicas y siguientes pasos |
| Predicciones | Explorador; Riesgos 2027 | Árbol sintético, supuestos y protocolo de emisión |
| Investigación | Mapa; Líneas y fuentes; Evidencia; Registro; Hitos | Estudios de demostración, Brier score, baselines y trazabilidad |
| Crear | Catálogo recuperado; Nuevas ideas; Estudio audiovisual | Cartera histórica institucional depurada (9 proyectos, 14 relaciones), borradores locales y guion de texto |

**Investigación institucional:** siete líneas de preguntas científicas con fuentes primarias, comparadores y condiciones pendientes. El CSV local permite comprobar fórmulas y un orden temporal declarado; la fecha real de publicación no se certifica y todavía no existe evidencia de utilidad predictiva prospectiva validada.

**Catálogo de ideas recuperado:** proviene del archivo histórico aportado al proceso de migración. Se publican nueve proyectos (cuatro vertientes V1–V4, tres aplicaciones y dos fichas de estructura), ocho fichas documentadas y catorce relaciones. La publicación usa una **proyección de campos permitidos**: elimina rutas, enlaces a PR antiguos, identificadores personales y referencias de implementación heredadas. Sus estados y fechas son históricos, no acreditan ejecución actual, nuevos experimentos ni pronósticos.

**Límites de esta versión:** no contiene los históricos reales, catálogos de países, predicciones de cohortes, modelos calibrados con observaciones oficiales ni los componentes de generación audiovisual. Tampoco permite escritura en un backend: las ideas se generan en memoria y pueden exportarse localmente. Ninguna cifra sintética es una previsión real.

## Cuaderno de investigación desde la web

La nueva ruta pública `/trabajo.html` ofrece una **herramienta local de investigación**, separada del conjunto sintético de divulgación. Permite importar archivos JSON privados elegidos por el usuario y verificar sus hashes SHA-256 en memoria, crear hipótesis no emitidas y exportar un cuaderno JSON. La política CSP bloquea las conexiones de red en esa ruta; el cuaderno **no lee Google Drive, no emite predicciones, no hace sellados RFC3161 y no es la custodia institucional canónica**. Para preservar una nueva actividad debe exportarse y admitirse explícitamente en el archivo institucional privado. No se almacena contenido privado en GitHub Pages ni en el repositorio.

### Comparación histórica por país

En el cuaderno `/trabajo.html` se puede importar un archivo JSON local que contenga los catálogos originales retrospectivos 2016 (195 países) y/o 2020 (196 países), ya sea en `futuresCatalogs` o dentro de las notas experimentales del archivo canónico de once tablas. Un validador rechaza catálogos parciales, variantes con metadatos inconsistentes y cualquier intento de tratarlos como emisiones prospectivas.

El panel **Árbol predictivo · comparación entre países** superpone de uno a seis países con colores, trazos y leyendas diferentes, compara las probabilidades anuales para el fenómeno seleccionado y permite inspeccionar sus cuatro estados `00/01/10/11`. El modelo por defecto utiliza conteos específicos de cada país con regularización global (`country_shrinkage`); otros modelos pueden coincidir exactamente para países con igual estado de origen y eso se representa sin alterar los resultados. Los gráficos se calculan únicamente en memoria desde los archivos que aporta el usuario; no se suben países, trayectorias ni probabilidades privadas a GitHub Pages o Drive. Son resultados **retrospectivos sobre una edición revisada**, no emisiones acreditadas ni evidencia de habilidad prospectiva.

## Árbol de países sin importaciones manuales

La vista **Predicciones → Explorador** utiliza desplegables de **Sociedad, Pregunta, Origen, Modelo y Año**. Obtiene automáticamente un fichero estático de distribución pública, generado en CI desde el **CSV oficial UCDP OrganizedViolenceCY 26.1** (CC BY 4.0, 7.132 filas), con la edición y la suma SHA-256 documentadas. El script `scripts/build_official_countries.py` computa por separado los conteos de transición a partir de los países presentes en cada fecha de corte (2014 y 2018): no carga expedientes del laboratorio privado, no usa resultados después del corte para ajustar parámetros, y no traslada identificadores ni textos de archivos personales. El resultado reproducible está disponible como `/data/countries-ucdp261.json` solo en GitHub Pages, nunca en el historial fuente.

**Distinción científica fundamental:** estos árboles son **reconstrucciones retrospectivas con la edición UCDP 26.1, publicada en 2026**, no predicciones prospectivas emitidas en 2016/2020 ni una copia certificada de los catálogos históricos privados. Para comparar cifras exactas del registro sellado original hay que seguir utilizando la custodia privada institucional.

## Inspección de ediciones históricas UCDP (10-11-2026)

La fuente oficial publica un índice de ediciones históricas del conjunto **Intrastate Country Level Onset**. La utilidad `scripts/inspect_ucdp_archives.py` inspecciona dicho índice, lista las rutas efectivamente enlazadas y valida las ediciones 23.1 y 25.1 frente a sus hashes SHA-256 registrados. Produce solo estadísticas de metadatos (esquema, cobertura temporal, recuentos y hash), sin datos personales ni historiales por país. La inspección se ejecuta en un job independiente de PR y **no** forma parte de GitHub Pages.

**Restricción de inferencia**: la existencia actual de un archivo de edición antigua no prueba cuándo exactamente fue publicado ni si una versión 22.1 estaba disponible antes de 2023. Sin prueba de disponibilidad previa, un estudio a posteriori sigue siendo una comparación *cross-release* retrospectiva. No se certifica emisión prospectiva.

**Hallazgo reproducido en GitHub Actions 10-11-2026, ejecución 42848508792**: los CSV oficiales UCDP Onset 23.1 (12.161 país-año, hasta 2022) y 25.1 (12.553, hasta 2024) coinciden con las huellas SHA-256 institucionales. Comparando únicamente los 12.161 país-año hasta 2022, `onset2` cambia en **2 casos** (2018, 0→1; 2021, 1→0). No cambian la cobertura de países-año en el periodo común ni los **242** positivos agregados, aunque sí la identidad temporal de dos etiquetas. 1946–1989: 0 cambios; 1990–2009: 0; 2010–2020: 1; 2021–2022: 1.

El índice oficial incluye el CSV 24.1, pero su URL respondió **HTTP 404** en el job de investigación; la edición 22.1 no aparece enlazada. Este estado refleja únicamente esa comprobación puntual y puede cambiar si UCDP repara el archivo. Por ello **aún no es posible certificar una evaluación multianual point-in-time** usando la cadena de fuentes Onset prevista. El resultado de revisiones se publica en la sección *Investigación → Evidencia*, separado de las pruebas sintéticas y de la validación de capacidad predictiva.


## Q-GEO-01 · Auditoría de unidades y tasas recientes (10-11-2026)

**Revisión del estudio mixto de 715 países-año:** el archivo `onsets_computed.csv` enlazado como Onset 19.1 contiene 47 duplicados país-año, 13 discordantes. El conjunto posterior **Intrastate Country Level Onset** exige por diseño un único registro por país-año. Agregar las observaciones antiguas con OR no certifica equivalencia de las etiquetas ni de los países en riesgo. Por consiguiente, el resultado −8,94 % de aquel experimento permanece **solo como diagnóstico exploratorio de archivos heterogéneos** y no debe citarse como validación independiente comparable. Véase la documentación de UCDP sobre niveles *conflict* y *country* en `https://ucdp.uu.se/downloads/onset/ucdp-codebook-onset-221.pdf`.

Para evitar el cambio de unidad, `scripts/experiment_recency_onset.py` utiliza **únicamente las ediciones Intrastate Country Level 23.1 y 25.1**, comprobadas por SHA-256. La rejilla fija de candidatos, planteada **después** de mirar los primeros resultados, compara las tasas globales calculadas sobre 5, 10, 20 años e histórico completo; aplica también un modelo regularizado por país con prior 20 sobre cada una de esas tasas. Presenta los ocho modelos en su totalidad y **no selecciona** el mejor para alegar una prueba nueva.

| Muestra | N país-año | Inicios `onset2` | Precaución |
|---|---:|---:|---|
| Ventanas internas 2015–2022 | 1.568 | 22 | Edición 23.1 revisada, **no as-of** |
| Comparación externa 2024 | 196 | 1 | Edición 25.1 como etiquetas, **resultado ya visto** |

En el contraste externo de 2024, el Brier de la **frecuencia global 5 años** es **0,005142209**, ligeramente inferior al global histórico **0,005201040**. El Brier del **modelo por país con prior de 5 años** es **0,005285406**, peor que el global. En la muestra interna, el Brier agregado del global completo es **0,013845771**, frente a **0,013888438** del modelo por país completo. Con un solo inicio en 2024, seleccionar un vencedor entre ocho variantes equivaldría a *selection bias*. El log-loss puede ordenar los modelos de forma diferente y se muestra por separado.

**Pruebas y trazabilidad:** Actions `42859240878`, scripts `experiment_recency_onset.py` / `test_experiment_recency_onset.py`; la investigación pública expone agregados en `data/research.json`. El experimento retrospectivo no contiene emisiones; la nueva cohorte GEO-2027 es independiente, está emitida y tiene 0 resultados resueltos. No hay pruebas confirmatorias nuevas. Próximo paso científicamente defendible: emitir y sellar prospectivamente predicciones antes de un nuevo periodo objetivo y validarlas cuando se publiquen resultados.

## Q-GEO-01 · Contraste real entre ediciones 2017/2022 (10-11-2026)

La herramienta institucional `scripts/run_legacy_vintage_holdout.py` calcula, sin descargar ni publicar datos del repositorio personal, un experimento **ex post** con tres CSV históricos oficiales UCDP verificados por SHA-256. Ajusta tasas globales y por país (regularización 20) desde 2000 hasta el último año **realmente contenido** en cada archivo, sin utilizar las etiquetas del año objetivo durante el entrenamiento. Compara 2020–2022 (archivo enlazado bajo Onset 19.1 → resultados de 23.1) y 2024 (23.1 → 25.1).

| Año | Países-año | Inicios `onset2` |
|---|---:|---:|
| 2020 | 173 | 2 |
| 2021 | 173 | 1 |
| 2022 | 173 | 3 |
| 2024 | 196 | 1 |
| **Total** | **715** | **7** |

**Resultado descriptivo NO HOMOGÉNEO**: los ficheros pueden utilizar unidades de observación distintas. Sus resultados no constituyen una prueba válida de capacidad prospectiva comparable. Brier del modelo por país **0,011100848419**, baseline de frecuencia global **0,010190138316**, referencia trivial siempre cero **0,009790209790**; Brier Skill frente a global **−8,94 %**. Log-loss del modelo **0,067702071233**, global **0,064953305637**. El intervalo exploratorio mediante 2.000 bootstrap por país para Brier país menos global fue **[+0,000199329, +0,001657918]**. Esto no permite afirmar superioridad y no constituye validación confirmatoria.

**Limitaciones materiales que no deben ocultarse:** el CSV que UCDP enlaza bajo 19.1 termina realmente en **2017**, aunque su codebook se refiere a 2018. Contiene **47 claves país-año duplicadas**, 13 con `onset2` contradictorio. Se aplicó una transformación OR («al menos un inicio») y, como sensibilidad exploratoria post hoc, se excluyeron todas las claves duplicadas: 516 observaciones, Brier Skill **−7,43 %**. La limpieza modifica la población al perder un país de referencia; no se presenta como prueba confirmatoria. No hay certificación criptográfica de las fechas de publicación originales, ni se garantiza paridad completa de las definiciones entre ediciones, ni se emitieron pronósticos en los años objetivo.

Experimento reproducible: ejecución de Actions `42856960583`, pruebas `scripts/test_run_legacy_vintage_holdout.py` y estudio agregado `data/research.json` (`external_vintage_holdout`). La web solo publica métricas agregadas, fuentes y advertencias. **Pronósticos prospectivos verificados: 0**.

## Evaluación temporal Q-GEO-01 (experimental)

`src/temporal-validation.mjs` implementa un evaluador **offline** de país-año mediante rolling-origin, con ventana de test predefinida, embargo de etiquetas, disponibilidad declarada de fuentes y estado previo, comparadores global y condicional, regularización jerárquica por país, métricas Brier/log-loss, calibración descriptiva y alertas con cupo fijo. Sus pruebas adversariales están en `tests/temporal-validation.test.mjs`.

**Este evaluador local no ha emitido predicciones verificadas**: sus pruebas de unidad siguen empleando ejemplos sintéticos; el contraste retrospectivo real entre ediciones se ejecuta mediante el script institucional independiente documentado en el apartado anterior. Las fechas y hashes de entrada no se autentican automáticamente: el resultado permanece etiquetado `RETROSPECTIVE_ROLLING_ORIGIN_ASOF_SELF_REPORTED`. No se publica el código del evaluador en Pages ni se mezclan archivos personales. El contraste real entre UCDP 23.1/25.1 de 2024 continúa siendo no concluyente: Brier peor y log-loss mejor que el baseline, con un solo evento.

## Ejecución

Sitio HTML/CSS/JS sin framework ni dependencias externas. Para previsualizarlo, servir la carpeta mediante un servidor estático (por ejemplo, `python3 -m http.server 8000`) y abrir la raíz del servidor. No abrir `index.html` directamente mediante `file://`, porque la carga del JSON usa `fetch`.

```bash
node --test tests/*.test.mjs
python3 scripts/audit_public.py
```

GitHub Actions ejecuta las pruebas, comprueba los autores, audita el árbol público y publica exclusivamente `index.html`, `styles.css`, `logo.svg`, `favicon.svg`, `src/site.mjs`, `src/metrics.mjs` y `data/demo.json`, así como `src/research.mjs` y `data/research.json`, además de `src/project-catalog.mjs`, `src/project-portfolio.mjs` y `data/projects.json` depurado. El paquete público incluye ahora además el manifiesto y las 196 probabilidades GEO-2027, con verificación de SHA-256. Ningún README, workflow, archivo de desarrollo o configuración de repositorio forma parte del paquete desplegado.

## Requisitos para datos reales

Toda observación requiere licencia de redistribución, fuente primaria, fecha de publicación, edición temporal recuperable y protocolo de evaluación. Los pronósticos necesitan fecha de emisión verificable anterior al desenlace y comparación con un baseline. Las evaluaciones retrospectivas no se presentarán como pruebas prospectivas.

El sitio es una demostración pública autocontenida: no incorpora credenciales, endpoints de acceso privado ni datasets experimentales. Se auditan sus activos y dependencias antes de cada publicación.

© IDEA LAB. Derechos reservados salvo indicación expresa.
