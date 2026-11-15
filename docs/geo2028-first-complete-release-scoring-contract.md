# GEO2028 — Contrato futuro de evaluación oficial

**Preparado el 15 de noviembre de 2026, antes de conocer resultados de 2028.** El contrato no calcula ni certifica hoy ninguna etiqueta de 2028. La primera emisión contiene **196 países GWNO**, con origen **2025**, horizonte **tres años**, variable anual binaria de violencia estatal UCDP OrganizedViolenceCY con umbral de 25 muertes.

## 1. Cadena de procedencia anterior al resultado

| Componente | Prueba inmutable |
|---|---|
| Pronóstico original | data/forecast-2028-geo3.json |
| SHA-256 de la emisión | fd5832c6896548b053202f2f84bd0f7cd4a75df44462fbd4f259b9d8d4c39bde |
| Primer commit público | 5a7c949f6fe9a352ecb27c4e4193f2f3e92b64d0 |
| Primer commit main que registra el protocolo, anterior a emitir números | 83c1be9a03f31c38993350b26ff0ff1e678cb0c5 |
| Archivo original UCDP 26.1, último año 2025 | SHA-256 66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34 |
| Emisión GEO2027 original, para comprobar continuidad | SHA-256 5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5 |

El evaluador verifica estas huellas, todos los GWNO originales, las probabilidades congeladas y la identidad de las preguntas 2027 sin volver a entrenar. **GEO2027 (2025→2027, horizonte dos años) y GEO2028 (2025→2028, horizonte tres años) comparten países y año de origen; no constituyen replicaciones independientes.**

## 2. Qué fuente futura puede generar un candidato de puntuación

No existe información anual completa de 2028 antes del 1 de enero de **2029**. Una fuente candidata deberá presentarse como ZIP oficial bajo la ruta HTTPS ucdp.uu.se/downloads/organizedviolencecy/organizedviolencecy-291-csv.zip, o versión posterior del mismo producto, con:

- SHA-256 aportado de **todos los bytes del ZIP** y comprobado localmente.
- Fecha real de publicación alegada posterior al 31/12/2028 y no posterior al día en que se comprueba.
- Encabezados inequívocos para país GWNO, año calendario y número de muertes estatales estimadas best; etiquetas únicamente para **2028**.
- Una única fila de 2028 por país, sin números negativos, campos vacíos, duplicados o valores ambiguos.
- Correspondencia completa de los **196 GWNO** emitidos en 2026. Un país sin etiqueta **no se convierte por defecto en un cero**.

El mero URL y las fechas suministradas por el operador, aunque parezcan oficiales, **no prueban** que se trate de la primera edición completa ni su fecha auténtica. Esa certificación requiere examen posterior e independiente de UCDP: publicación primaria, completitud de cobertura, convención de ausencias, posibles revisiones y correspondencias GWNO.

## 3. Puertas de cobertura y cálculo

**196 de 196 etiquetas explícitas obligatorias para cualquier score provisional.** Con 195/196 —o menos— el programa solo informa de cobertura, GWNO sin resolver y procedencia no certificada. No publica Brier parcial y no cambia el denominador.

Para las 196 etiquetas registradas, la medida principal preregistrada es:

\[
\Delta \mathrm{Brier}=\frac{1}{196}\sum_{i=1}^{196}\left[(p_{\mathrm{Markov\ país},i}-y_i)^2-(p_{\mathrm{global\ últimos5},i}-y_i)^2\right].
\]

Signo negativo: menor Brier del modelo primario **para esa única realización de 2028**, no superioridad estadística general. Se calcularán asimismo:

- Brier de los tres modelos **p_model**, **p_baseline_global_5y** y **p_global_markov_3step**.
- Diferencial Brier del primario respecto a Markov global; pérdida logarítmica descriptiva.
- Número observado de países que superan el umbral frente a **33,438734715114** países esperados según el modelo.
- Calibración descriptiva estratificada por estado 2025 (activo/inactivo) y cinco tramos fijos de probabilidad.

No se añaden intervalos bootstrap IID, valores p, inferencia de correlación real, migración automática de modelo ni tests independientes combinando GEO2027 con GEO2028. Son países expuestos a posibles shocks comunes; un año conjunto no representa 196 réplicas independientes.

## 4. Dos estados posibles: nunca certificación automática

El programa scripts/evaluate_geo2028_first_complete_official.py solo puede informar:

1. **SOURCE_PRESENT_COVERAGE_INCOMPLETE_UNCERTIFIED**: fuente futura admisible como candidata, faltan etiquetas y no se producen métricas.
2. **COMPLETE_196_SOURCE_CANDIDATE_UNCERTIFIED**: las 196 etiquetas existen en el candidato y se calculan puntuaciones provisionales, pero la autenticidad de *primera publicación anual completa* sigue pendiente de revisión externa.

En **ambos** estados, los indicadores first_complete_release_independently_attested, prospective_skill_demonstrated y automatic_primary_model_change_authorized son **false**. El evaluador no publica sus resultados en la interfaz ni modifica los pronósticos originales; el informe candidato se escribe exclusivamente **fuera del repositorio**.

La evidencia científica solo podrá declararse tras una certificación independiente y un análisis honesto de la dependencia entre países y entre años. Un buen Brier aislado no demuestra generalización.

## 5. Reproducción futura y comprobaciones actuales

La herramienta necesita seis parámetros: ruta a ZIP completo oficial, URL, SHA-256 real, fecha de publicación auténtica, ruta de salida fuera del repositorio y las emisiones inmutables ya incluidas en el proyecto. **No está autorizada a ejecutarse ahora con una edición inexistente de 2028**.

El job CI institucional usa únicamente tests sintéticos: rechaza fechas anteriores a 2029, versiones UCDP viejas, fuentes suplantadas, hashes mal formados, etiquetas duplicadas o ausentes, cambios de horizonte, reescritura del registro previo, intentos de autocertificación y supuestos de independencia. Una prueba sintética no equivale a un resultado futuro observado.

**Conclusión:** el contrato preparado hoy permite una evaluación provisional posterior, pero no fabrica datos 2028 ni otorga capacidad predictiva demostrada al modelo.
