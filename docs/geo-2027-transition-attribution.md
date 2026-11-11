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

## Resultado verificado con las fuentes originales

Ejecución fuente-separada en GitHub Actions con los SHA originales fijados; agregado publicado en `data/geo2027-transition-attribution-archival.json`. CI vuelve a comprobar que el informe sea **idéntico byte a byte** al que genera el script, sin exponer registros individuales.

| Segmento | País-años | Positivos (umbral >=25) | Brier modelo nacional | Brier Markov global |
|---|---:|---:|---:|---:|
| Todos | 392 | 69 | **0.04008406** | 0.04692112 |
| Sin estado activo al origen (ex ante) | 321 | 8 | 0.02264753 | 0.02521028 |
| Con estado activo al origen (ex ante) | 71 | 61 | 0.11891681 | 0.14507856 |
| Cambió el estado (ex post) | 18 | 8 | 0.62885871 | 0.67198768 |
| Estado estable (ex post) | 374 | 61 | 0.01174731 | 0.01683770 |

Hubo **8 entradas** de inactivo a activo y **10 salidas** de activo a inactivo. **Entrar en el estado de >=25 muertes por violencia estatal organizada no es un episodio `newconf` de UCDP, ni necesariamente una guerra que nunca existió antes.**

- Comparador duro de persistencia de origen `P=0/1`: Brier 0.04591837. Modelo nacional 0.04008406, mejora numérica de 0.00583431.
- La ventaja de Brier frente al Markov global es `-0.00683706`, de la que aproximadamente **71,0 %** procede de los **374 estados estables** (374/392 × 0.00509039) y **29,0 %** de los **18 cambios** (18/392 × 0.04312897). Es una descomposición contable posterior, **no una capacidad de seleccionar los cambios antes de que sucedan**.
- Sin conflicto al origen: probabilidad media prevista **0.04206** frente a frecuencia observada **0.02492**. Con conflicto al origen: previsión media **0.76662** frente a frecuencia observada **0.85915**. La calibración desagregada es desigual aunque los promedios globales sean similares.
- Intervalo bootstrap por país para (Brier nacional − Brier Markov global): sin conflicto al origen **[-0.00793, +0.00061]**, compatible con diferencia nula; con conflicto al origen **[-0.03922, -0.01164]**. Los intervalos no representan una certificación de validez estadística bajo shocks globales comunes.
- Por año objetivo: 2024, 4 entradas y 6 salidas; 2025, 4 entradas y 4 salidas. Un único objetivo anual no basta para demostrar que la descomposición sea estable en el tiempo.

**Decisión científica:** conservar la predicción GEO-2027 ya emitida sin recalibración ni cambios, y **no trasladar el buen Brier total a titulares de capacidad de detección de conflictos nuevos**. El nuevo subprograma útil es pronosticar específicamente **cambios de estado** sobre un umbral y validarlos con más cohortes fuente-separadas, pruebas de calibración condicional y costes de falsos positivos.

Este contraste es una reconstrucción retrospectiva, no un pronóstico históricamente registrado en su origen ni un resultado de 2027.
