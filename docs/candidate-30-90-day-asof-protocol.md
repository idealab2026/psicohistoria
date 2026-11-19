# Q-CANDIDATE · Inicio de línea prospectiva de 30 y 90 días (19-11-2026)

**Estado: SOURCE-VINTAGE GATE IMPLEMENTADO · SIN MODELO CALIBRADO · SIN EMISIÓN.**

Este documento NO es una predicción de violencia real ni una evaluación prospectiva. Conserva
inalteradas las emisiones GEO2027, NEWCONF2027, ACD2027 y GEO2028. El primer paso es
evitar la trampa metodológica de reconstruir retrospectivamente entradas con datos revisados
y presentarlas como si estuvieran disponibles el día original.

## Fuente y disponibilidad verificada

- Fuente institucional: [UCDP Candidate Events Dataset](https://ucdp.uu.se/downloads/),
  basada en GED y publicada por ediciones mensuales provisionales.
- Catálogo histórico oficial: <https://ucdp.uu.se/downloads/olddw.html>.
  Archiva ediciones mensuales y acumulados trimestrales de 2024, 2025 y 2026.
- En la consulta realizada el 19/11/2026, el catálogo y la documentación API mostraban
  como última edición mensual **26.0.9 (septiembre 2026)** y acumulado enero-septiembre
  **26.01.26.09**. Este hecho NO permite deducir una fecha original de primera publicación.
- La cobertura global anunciada es provisional: una ausencia de evento en Candidate NO
  acredita ausencia real de violencia ni puede sustituir a la base anual definitiva GED.
- Se debe verificar con bytes originales y codebook la correspondencia de columnas,
  identificadores país, deduplicación entre ediciones, precisión temporal y diferencias
  de codificación con GED antes de puntuar un solo caso real.

## Una pregunta operacional, no «predecir guerras» en general

Horizontes predeclarados: **30 y 90 días naturales** después de la emisión, sin solapar
el propio día de emisión. La pregunta candidata es: «¿registrará UCDP Candidate una
escalada significativa de violencia organizada estatal en el país durante ese horizonte?».

**Propuesta pendiente de validación, NO etiqueta definitiva:** para un país i y horizonte h,
sumar los fallecidos `best` de eventos estatales de tipo 1 cuyo `date_end` caiga dentro
de la ventana futura; definir escalada si el total es al menos 10 y al menos el doble del
nivel previo escalado al horizonte (últimos 90 días informativos, con suelo 1).
Esta propuesta tiene un umbral convencional; hay que contrastar su tasa base, ruido
de recuentos, multi-day events, cobertura provisional y sentido operativo antes de fijarla.
No se debe confundir con guerra nueva, cambio político o violencia civil total.

El universo inicial se propone de 196 GWNO para comparación con el resto del laboratorio,
PERO la equivalencia entre códigos GED Candidate y GWNO anual necesita una comprobación
explícita. **No rellenar ausencias país como cero** antes de verificar cobertura global.
No hay ninguna probabilidad pública emitida para esta pregunta a fecha del documento.

## Primer artefacto implementado: auditor de elegibilidad as-of

`scripts/check_ucdp_candidate_asof.py` acepta un archivo CSV auténtico, su manifiesto,
la fecha de emisión y el horizonte. Su respuesta `SOURCE_ELIGIBLE_NO_FORECAST` solo
indica que las condiciones formales enumeradas se cumplen. **No calcula probabilidades**.

Exige conjuntamente:

1. URL oficial exacta y versión deducida del nombre, incluyendo si es edición de un mes
   o acumulado trimestral. Impide declarar tres meses de historia usando solo el archivo
   individual de septiembre.
2. Cobertura de al menos 90 días; publicación declarada posterior al período fuente
   y anterior al día de emisión; desfase entre fecha de emisión y último día cubierto
   no mayor de 45 días. La vigencia no se deduce de la fecha de consulta.
3. SHA-256 íntegro de los bytes originales; revisión de fecha de publicación avalada
   por una referencia HTTPS institucional; no acepta autoafirmaciones «sin revisión».
   **La attestation del operador NO verifica automáticamente que la fecha sea cierta**.
4. CSV UTF-8 y campos GED obligatorios; ID de evento único, fechas coherentes,
   códigos y muertes válidos, prohibición de introducir eventos posteriores al
   período cubierto, fuente no vacía. El archivo se lee entero, sin observar resultados.
5. No incorpora datos posteriores a la fecha de emisión, no puntúa etiquetas, no añade
   registros al árbol de predicciones, no altera ninguna cohorte congelada.

Ejecución local o CI con archivo real y manifiesto revisado:

```sh
python3 -B scripts/check_ucdp_candidate_asof.py \
  --source /ruta/original.csv --manifest /ruta/manifiesto.json \
  --issued-on 2026-11-19 --horizon-days 30
```

Este ejemplo **no afirma que exista** manifiesto certificado ni que la versión de
septiembre pase el filtro. De hecho el acumulado que termina el 30/09/2026 está a
50 días del 19/11/2026, por encima del máximo de 45: el verificador lo bloqueará.
La fecha exacta de primera publicación también sigue sin acreditarse externamente.

## Evaluación exigida antes de producir decisiones

Secuencia vinculante para el siguiente desarrollo:

1. **Fechas/versión:** descargar y verificar los archivos originales 2024–2026,
   recuperar pruebas independientes de fechas de publicación y registrar SHA de cada
   vintage. No asumir que la URL histórica implica disponibilidad contemporánea.
2. **Estimando y cobertura:** inspeccionar el codebook y una muestra de eventos
   multidiarios, construir el panel mensual de países con trazabilidad de
   eventos omitidos/revisados; decidir *antes de puntuar* la etiqueta definitiva,
   las reglas de deduplicación y la exclusión de cortes temporales ambiguos.
3. **Baselines:** persistencia del nivel reciente, prevalencia histórica y modelo
   simple regularizado; ningún ML complejo sin ganancia sobre esos controles.
   Comparar Brier, log-loss, calibración y ranking dentro de cada horizonte.
4. **Evaluación as-of:** separar por fecha de edición efectivamente disponible;
   evitar leakage por revisiones; bloques temporales no IID y dependencia regional;
   medir retardo y sesgo de revisiones de Candidate a GED anual.
5. **Primera emisión:** publicar antes del resultado objetivos, universo, 196
   probabilidades, baselines, fecha verificable, hash del CSV del origen, fecha y
   código exacto. Solo entonces habilitar la evaluación prospectiva.

Un resultado reconstruido a posteriori llevará etiqueta **exploratorio histórico**;
un resultado futuro, hasta la certificación de la edición objetivo, será **pendiente**.

## Privacidad y reproducibilidad

Los artefactos públicos contienen solo código y fuentes de UCDP; no nombres personales,
correos privados, repositorios personales, tokens ni datos internos. El control institucional
`scripts/audit_public.py` y las pruebas adversariales deben pasar en CI. Las fuentes
institucionales UCDP requieren cita de la fuente y atribución CC BY 4.0; esta investigación
no redistribuye aún registros de víctimas ni contenidos periodísticos.

**Decisión científica:** no convertir artificialmente un sistema de comprobación de
fuentes en un sistema que «ya predice». El siguiente hito real es un backtest completo
con ediciones contemporáneas y un endpoint que merezca la pena anticipar.
