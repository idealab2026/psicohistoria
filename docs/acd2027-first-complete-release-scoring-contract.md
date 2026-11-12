# ACD-2027 — Contrato de resolución futura con la primera edición oficial completa

**Protocolo publicado en 2026, antes de observar resultados de 2027.** Solo establece cómo puntuar una predicción ya emitida. No aporta ninguna observación nueva.

## Emisión y variable a evaluar

El compromiso público `PSICO-ACD2027-INTRASTATE-T2-PERSISTENCE-V1` quedó emitido con los **32 códigos GWNO** de países con al menos un conflicto intraestatal UCDP/PRIO ACD de tipo 3 o 4 registrado en 2025. El primer commit público es `41db7bd154e0140ced15abd8727a7d52d998852c`, y la huella SHA-256 de sus probabilidades es `6cf7d0340a4c25062af7a040586fb6a73a98c9e6ab80473527171c0a5a963d9c`. Las **tres** probabilidades individuales son inmutables: primario global reciente `p_global_recent5`, secundarios `p_country_eb` y `p_lag1_group`.

**Objetivo**: ¿se registra en el país algún conflicto intraestatal UCDP/PRIO ACD de tipo 3/4 durante **2027**? No se exige que sea el mismo conflicto individual de 2025, no representa el umbral de muertes del modelo GEO-2027, ni onset, ni prueba de paz.

## Fecha de disponibilidad y procedencia

El primer corte anual oficial que *podría* cubrir 2027 es una edición ACD publicada **en 2028 o después**, previsiblemente la **28.1**, en forma de un único ZIP CSV `https://ucdp.uu.se/downloads/ucdpprio/ucdp-prio-acd-281-csv.zip`. Esta ruta es **una expectativa de nomenclatura, no una URL cuya publicación ya esté verificada**. No debe descargarse ni usarse antes de que UCDP la publique.

El evaluador `scripts/evaluate_acd2027_retention_official.py` requiere todos los argumentos explícitos: ZIP local de origen, **URL institucional exacta**, hash SHA-256 calculado sobre los bytes del ZIP, fecha declarada de publicación **no anterior a 2028-01-01**, y una ruta de salida que no puede sobrescribir los compromisos originales. Ni el URL ni la fecha aportados por un operador certifican por sí solos que la fuente esté publicada, sea **la primera** o cubra íntegramente el año. El programa emite solo resultados con estatus `CANDIDATE_UNCERTIFIED`. La **certificación de primera fuente anual completa, su fecha y cobertura debe realizarse independientemente** antes de presentar cualquier puntuación como resultado válido.

Si la primera edición completa tiene una nomenclatura distinta de la esperada, hay que auditar explícitamente esa excepción **antes** de introducir resultados. No se sustituirá silenciosamente la primera edición por una posterior.

## Política de ausencias: cero ≠ dato faltante

ACD es una tabla de **conflicto-año**, no un panel de 196 países × años con ceros explícitos. Para puntuar la ausencia de conflicto en un país en 2027, hay que demostrar que el código de ese país aparece al menos una vez en la fuente histórica completa recibida; de otro modo, una ausencia podría significar una pérdida de cobertura o recodificación, no un verdadero cero.

Se cuentan los **32 códigos originales** sin alterar su numerador ni denominador. Una referencia presente en la fuente histórica sin registro de conflicto intraestatal en 2027 permite asignar **provisionalmente** etiqueta cero *solo como candidato* y sujeto a confirmación externa de cobertura. Si falta cualquiera de los 32 identificadores en el histórico de la fuente objetivo, o aparece algún registro intraestatal de 2027 con gobierno/localización ambiguos, o un tipo de conflicto nuevo/no reconocido, el script devuelve `INSUFFICIENT_SOURCE_COVERAGE_NO_SCORE` y deja las **tres métricas nulas**. Rechaza años futuros dentro de la edición supuestamente 28.1, conflictos duplicados y ZIP sin ningún registro de 2027.

Esta regla **no elimina** toda la incertidumbre sobre cobertura de países sin registros en 2027: ver un código en años anteriores no prueba por sí solo que ese país haya tenido reporting completo durante todo 2027. Por eso, incluso con los 32 códigos reconocidos, las métricas **no están certificadas independientemente**.

## Métricas congeladas y comparación permitida

Solo cuando se dispone de 32 etiquetas provisionales calculables, se obtienen, en el **mismo conjunto completo y sin reentrenar**, el Brier medio y log-loss medio de las tres probabilidades emitidas en 2026:

\[
\operatorname{Brier}_{m} = \frac{1}{32}\sum_{i=1}^{32} (p_{m,i}-y_i)^2, \qquad
\operatorname{LogLoss}_{m} = -\frac{1}{32}\sum_{i=1}^{32} [y_i\ln p_{m,i}+(1-y_i)\ln(1-p_{m,i})].
\]

La métrica primaria es el Brier del modelo **global reciente**. Se notificará la diferencia de Brier y log-loss de cada modelo secundario **menos** el primario: valores negativos favorecen al secundario. También se mostrarán el número total de persistencias observadas y las sumas de probabilidades originales; **no** se usará la mejor submuestra de países como denominador alternativo.

**No** se publicará un contraste IID por país como p-valor inferencial: los países están correlacionados, la muestra es pequeña y la selección de modelos secundarios siguió la exploración retrospectiva. Incluso un Brier mejor en 2027 no implica automáticamente significación estadística ni superioridad generalizable. Las comparaciones con GEO-2027 y NEWCONF-2027 tienen variables objetivo distintas y no se deben presentar como una competición de métricas idénticas.

## Auditoría en 2026

La invocación `--audit-issuance` comprueba **solo la primera emisión histórica y sus 32 probabilidades**: SHA-256, hash Git del generador, primer commit público, manifiesto y auditoría congelada. No descarga, simula ni utiliza ningún resultado oficial de 2027. Los tests del nuevo evaluador utilizan únicamente **ZIP sintéticos** (escenarios completos, incompletos, años imposibles, duplicados, fechas falsas, formatos nuevos y ataques de procedencia) y comprueban que una pérdida de cobertura impide puntuar.

Esta línea de resolución futura **no debe ejecutarse como búsqueda periódica ni producir scores en 2026**. Los resultados de 2027 permanecen sin observar. No se cambia el archivo original ACD, ni GEO-2027, su shadow, las 15 alertas o NEWCONF.
