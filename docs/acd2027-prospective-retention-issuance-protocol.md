# ACD-2027 — Primera cohorte de persistencia intraestatal emitida antes de observar 2027

**Preparación: 12 de noviembre de 2026.** El timestamp de emisión válido será el del primer commit público del JSON canónico completo; ni este texto ni una predicción publicada posteriormente pueden asignarle una fecha anterior.

## Definición exacta y separada de GEO

Fuente original: **UCDP/PRIO Armed Conflict Dataset v26.1**, con observaciones hasta el año **2025**, descargada del dominio institucional `ucdp.uu.se` mediante ZIP CSV oficial. Solo se incluyen filas de conflicto intraestatal (UCDP `type_of_conflict∈{3,4}`) con identificador único `gwno_a=gwno_loc`, sin reasignar partes con códigos múltiples.

**Conjunto de riesgo fijo:** todos los países con al menos un conflicto intraestatal de tipo 3/4 registrado en 2025. **Resultado objetivo para 2027:** existencia de al menos un conflicto intraestatal ACD de los mismos tipos registrado en el mismo país durante 2027, según la **primera edición oficial anual completa de UCDP/PRIO ACD que cubra 2027**. Un resultado cero no implica ausencia de otras violencias ni una paz negociada; un resultado uno puede corresponder a **otro conflicto** distinto de aquel registrado en 2025.

No es la variable **GEO-2027** de más de 25 muertes por violencia estatal en un país-año. Tampoco es NEWCONF, ni un modelo de comienzos de conflicto, ni una predicción para todos los países del mundo. Ninguna fuente de 2026 parcial ni etiqueta de 2027 entra en el modelo.

## Tres probabilidades publicadas por país

Todos los modelos usan exclusivamente los conflictos registrados en la edición 26.1 hasta 2025. Para los históricos se forman pares país-origen `(i,y)` con conflicto intraestatal registrado en `y`, desde **1990** y con objetivo `y+2` completamente observable en 2025. El último año de origen de entrenamiento permitido es **2023**.

- **Primario, tasa global reciente de cinco años:** tasa empírica de persistencia a dos años de los países activos en años de origen **2019–2023**. Suavizado Jeffreys de 0,5 éxitos y 0,5 fracasos, fijado a partir de la investigación histórica. Todos los países reciben la misma probabilidad primaria; constituye una referencia de calibración, **no un ranking individual**.
- **Secundario, historial de país:** tasa de persistencia país a dos años desde 1990, regularizada con 12 pseudocuentas de la tasa global histórica.
- **Secundario, actividad previa:** tasa histórica de persistencia condicional a si el país tenía otro registro de conflicto en 2024 (`t−1`), regularizada con 12 pseudocuentas de la tasa global histórica.

Los tres modelos y sus hiperparámetros son exactamente los empleados en el backtest retrospectivo ACD de la PR #62. Se elige el primario **antes del objetivo 2027** tras comprobar en la PR #63 que el pequeño beneficio histórico de actividad previa cambia de signo al excluir determinados años: **la selección del método no es independiente de los resultados históricos previamente examinados**.

Se publicará una fila por código GWNO de país activo en 2025, con las tres probabilidades redondeadas a 12 decimales, el estado registrado en 2024 y los ejemplos históricos de ese país. El número de países se fijará a partir de la descarga auténtica, sin forzar que haya 196.

## Protocolo de evaluación futura, fijado antes de observar el resultado

La evaluación **primaria** es el **Brier medio** de la tasa global reciente en el conjunto exacto de países fijado en el primer commit público, comparado con el Brier del modelo de historial de país y con el modelo de actividad previa de forma secundaria. También se publicará **log-loss** de los tres.

La puntuación solo se certificará una vez obtenida y fechada de forma independiente la **primera edición anual completa oficial que cubra 2027**, y siempre con la misma lista de países de origen. Si falta el código de un país en la cobertura oficial o no se puede distinguir entre ausencia de conflicto y ausencia de observación, no se publicará un Brier definitivo; se preservará un estado **pendiente**.

Se publicarán puntuaciones por año de emisión y país únicamente **después de verificar el resultado de 2027**, nunca usando datos parciales de 2026 para cambiar las probabilidades. No se anunciarán p-valores IID: los países pueden compartir shocks y sus evaluaciones anteriores se solapan temporalmente.

**No se fija una hipótesis confirmatoria de superioridad** del secundario: sería engañoso después de haber examinado su ventaja histórica y su fragilidad. Se fija antes de 2027 el criterio comparativo y el orden de importancia de métricas, no una garantía de habilidad predictiva.

## Emisión, trazabilidad y privacidad

La primera fase `--probe-source` descubre la huella SHA-256 real del ZIP de la edición 26.1, sin publicar probabilidades. La segunda fase exige que dicha huella esté fijada **en el código**, descarga nuevamente los bytes oficiales, autentica el corte 2025 y genera un JSON determinista en `data/forecast-2027-acd-retention.json`. Se auditará su igualdad de bytes desde GitHub Actions. El primer commit público de ese JSON —y no una fecha escrita por el operador— certificará su emisión; después se registrarán un manifiesto de emisión y una auditoría que impidan cambiar las probabilidades.

El estudio no incorpora ninguna referencia a repositorios personales ni modifica las probabilidades GEO-2027 originales o shadow, las 15 alertas emitidas ni NEWCONF-2027.

**Estado de resultados observados del objetivo 2027:** cero. La predicción solo tendrá validez prospectiva del **resultado futuro**, no validación independiente de la elección histórica de método.
