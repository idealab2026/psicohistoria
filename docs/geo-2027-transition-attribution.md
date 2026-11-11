# PSICOHISTORIA — GEO-2027 · Auditoría del cambio real frente a la persistencia

**11 de noviembre de 2026 · Diseño de análisis histórico, no emisión prospectiva nueva.**

## Pregunta científica

El Brier de un modelo de conflicto activo puede ser muy bajo si acierta la mayoría de países que nunca cambian de estado. Queremos distinguir:

1. **Estados estables**: sin conflicto en origen ni en objetivo, o con conflicto en ambos.
2. **Apariciones**: ausencia de violencia estatal armada >=25 muertes en el origen, presencia en objetivo.
3. **Resoluciones**: presencia en origen, ausencia en objetivo.

La pregunta no es «¿el modelo acierta más que una referencia de prevalencia global?», sino **«¿anticipa mejor que el Markov global y que la mera persistencia los cambios de estado?»**.

### Regla de la etiqueta

`UCDP OrganizedViolenceCY sb_total_deaths_best >= 25` para una pareja país-año, con la misma semántica del GEO-2027 registrado. Esto **no** es inicio de un nuevo conflicto (`newconf`) ni `onset2`; tampoco supone nuevas guerras, número de episodios, todos los tipos de violencia ni una predicción política individual.

### Diseño sin filtración

Se reproducen las ecuaciones del modelo original **sin alterar parámetros** para dos cortes cronológicos y entre ediciones de fuente diferentes:

| Modelo al origen | Fuente y último año permitido | Etiqueta posterior |
|---|---|---|
| 2022 → 2024 | UCDP OrganizedViolenceCY **23.1** (hasta 2022) | UCDP **25.1** (2024) |
| 2023 → 2025 | UCDP OrganizedViolenceCY **24.1** (hasta 2023) | UCDP **26.1** (2025) |

Todos los ZIP/XLSX se descargan de los URL oficiales y se cotejan con sus SHA-256 ya fijados en `scripts/backtest_archived_country_vintages.py`. No se entrena con ninguna etiqueta de la edición posterior; se añade **solo el año objetivo** a la vista necesaria para puntuación, mientras el estimador corta el entrenamiento en el origen.

196 países en cada uno de los dos cortes y **392 evaluaciones**, con **69 positivos** en el informe histórico previamente publicado. Una ausencia de etiqueta en la fuente posterior **invalida** el análisis: jamás se interpreta como 0.

### Comparaciones sin selección ex post

- Modelo nacional Markov de dos pasos, misma receta y shrinkage 20 del pronóstico de 2027.
- Markov global de dos pasos, misma fuente y mismo horizonte.
- Prevalencia global de cinco años.
- Referencia adicional y difícil: **persistencia determinista del estado conocido en el origen**, usando probabilidades 0 o 1 y Brier (no log-loss).

El informe distingue los siguientes grupos:

- **Ex ante**, identificables en el momento de origen: países sin conflicto y países con conflicto.
- **Ex post**, conociendo la verdad posterior: casos que cambiaron de estado y casos que no. Esta descomposición es *solo diagnóstica*: no es un segmento observable en el momento de predecir, por lo que un buen resultado dentro de él no equivale a una estrategia de alertas.
- Por año objetivo 2024 y 2025, para detectar dependencia de una única cohorte.

Se incluyen Brier, diferencia frente a Markov global, tasa observada frente a probabilidad media y bootstrap por país en cada grupo **ex ante**. No hay optimización de umbrales, elección del año vencedor ni ajuste de modelos después de observar las etiquetas.

### Criterios de interpretación y protección

Un modelo puede superar a la prevalencia global por persistencia y, a la vez, **tener un fallo grave al detectar entradas o salidas del conflicto**. Los grupos evaluados por resultado futuro presentan sesgo de selección si se interpretan como habilidad predictiva; por eso aparecen explícitamente marcados como retrospectivos.

La validación por ediciones archivadas es mejor que usar una edición revisada única, pero los documentos **no fueron emitidos históricamente** y no existe una notaría externa del instante real de disponibilidad de cada descarga. El bootstrap nacional no recoge shocks comunes y hay solo dos años objetivo.

No se tocan los documentos, hashes, manifiestos, parámetros ni contratos de resolución de **GEO-2027** ni **NEWCONF-2027**, y no se observa ningún resultado 2027. El estudio produce únicamente **agregados** sin registros identificables de países.

**Se publica un resultado solo después de que GitHub Actions reproduzca los valores de las fuentes originales y la auditoría institucional y de privacidad resulte satisfactoria.**
