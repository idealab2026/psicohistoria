# GEO · Túnez 2017: identificabilidad del estimando frente a revisiones del estado inicial

**Fecha:** 2026-11-17. **Naturaleza:** interpretación analítica de los resultados oficiales SHA-verificados de la PR #114; no es una emisión de pronóstico, una nueva descarga de UCDP ni una prueba de desempeño ex ante.

## Pregunta

¿Se puede llamar «fallo del pronóstico de salida» a una transición 2016→2017 cuyo estado inicial **cambió retroactivamente entre ediciones de la fuente**?

**Respuesta:** no sin especificar (a) la edición efectivamente disponible al emitir, (b) la variable predicha y (c) la edición que resuelve el resultado. La salida condicional, la inactividad de 2017 y la clasificación retrospectiva 10 son estimandos distintos.

## Evidencia institucional ya verificada

Fuente: [auditoría UCDP de siete ediciones](geo-tunisia-original-2017-exit-audit.md); artefacto fuente [JSON íntegro](../data/geo-tunisia-original-2017-exit-vintage-diagnostic.json).

| Edición GED | 2016, muertes tipo 1 best | 2017, muertes tipo 1 best | Estado de origen | Transición observada |
|---|---:|---:|---|---|
| 17.1 | 0 registradas | no disponible | 0 codificado | no evaluable |
| 18.1 | 72 | 3 | 1 | 10 |
| 19.1 | 72 | 3 | 1 | 10 |
| 20.1 | 72 | 3 | 1 | 10 |
| 21.1 | 69 | 0 | 1 | 10 |
| 22.1 | 88 | 15 | 1 | 10 |
| 23.1 | 88 | 15 | 1 | 10 |

Estados: 1 significa `best ≥ 25` muertes estatales país-año según una **edición**; 0 es `best < 25` codificado y **no significa ausencia demostrada de violencia**.

## Tres objetos probabilísticos que no se deben confundir

Escribimos `X_t^(v)` para el estado país-año codificado con la edición `v`, `I_t` para la información efectivamente accesible en la fecha del pronóstico, y `M_v` para un modelo reconstruido con `v`.

1. **Estado siguiente:** `P(X_2017=0 | I_2016)`. Una evaluación prospectiva requiere especificar antes del desenlace cómo se define `X_2017` y qué edición futura lo fija. Es una predicción válida incluso si la condición inicial fue codificada 0.
2. **Salida condicionada al origen activo:** `P(X_2017=0 | X_2016=1, I_2016)`. Su dominio requiere que el estado inicial esté clasificado activo **con los datos de origen admitidos por el protocolo**. Bajo GED17.1, Túnez no pertenece a ese conjunto condicionado: no asignar una probabilidad ficticia.
3. **Transición 10 retrospectiva:** `1{X_2016^(v)=1 y X_2017^(v)=0}`. Es una etiqueta conjunta por edición; cambia si la edición reclasifica el origen, aun manteniendo idéntico estado final.

Comparar (1) con (2) o tratar (3) como una predicción emitida en 2016 no es metodológicamente válido.

## Contrafactual cuantitativo, expresamente NO prospectivo

El JSON auditado registra para el origen 2016, GED17.1, `q_0 = P(X_2017=1 | X_2016=0) = 0.013654473546895802` en el Markov homogéneo reconstruido con soporte CY23 posterior.

En consecuencia, **si** se mantiene la etiqueta GED17.1 de origen inactivo, el mismo modelo reconstruido asigna:

`P(X_2017=0 | X_2016^(GED17.1)=0, M_GED17.1) = 1 - q_0 = 0.9863455264531042`, esto es **98,63 %**.

La etiqueta final 2017 de GED18.1–23.1 es 0 en todas las ediciones. Así, esta reconstrucción **acierta el estado final más probable**, aunque **no predice una salida desde estado activo**, porque el origen usado era 0. No hay contradicción: **el resultado final es estable y la transición de origen no**.

En contraste, la reconstrucción GED18.1 del escenario con origen activo proporciona `P(X_2017=0 | X_2016=1) = 0.182630906769` (**18,26 %**). Es otro estimando, bajo otra edición, publicada tras el objetivo, y por ello **no se puede comparar como si fueran dos pronósticos prospectivos rivales**.

**Advertencias que invalidan la lectura como habilidad predictiva:** GED17.1 se publicó en 2017, no estaba disponible en 2016; su reconstrucción usa el soporte país-año CY23.1 posterior, y el parámetro modelado se reestima a posteriori. Además, GED18.1 incorpora información del resultado 2017. El número 98,63 % es **solo una identidad diagnóstica derivada de un modelo retrospectivo**, no una probabilidad verdaderamente emitida en 2016.

## Nuevo criterio de identificabilidad para estudios retrospectivos

Antes de publicar un «acierto» o «fallo» de transición, exigir estas columnas por caso:

| Campo requerido | Regla |
|---|---|
| `forecast_issued_at_utc` | Fecha de emisión acreditable; nulo si no existe evidencia |
| `forecast_artifact_sha256` | Huella de un pronóstico original; nulo para reconstrucciones |
| `source_vintage_asof` | Edición publicada antes de la emisión, no solo año máximo de datos |
| `origin_state_asof` | 0 / 1 / desconocido según fuente disponible entonces |
| `origin_state_resolution` | 0 / 1 según edición usada para evaluar |
| `target_state_resolution` | 0 / 1 según edición usada para evaluar |
| `estimand` | Estado final, transición conjunta, salida condicionada o primer paso exacto |
| `origin_revision_flag` | Verdadero si el estado inicial difiere entre origen y resolución |
| `prospective_grade` | `CERTIFIED` solo con fuente disponible, artefacto fechado y regla de resolución precomprometida; en otro caso `RETROSPECTIVE_ONLY` |

**Regla de bloqueo:** si `origin_revision_flag=true`, no calificar un error de «salida condicionada» usando únicamente el estado revisado sin reconstruir la elegibilidad ex ante. Si `source_vintage_asof` es posterior a la emisión, no mostrar puntuaciones como validación prospectiva.

### Aplicación a Túnez

- El estado de origen cambia de 0 (GED17.1) a 1 (GED18.1).
- El estado de 2017 es 0 para GED18.1–23.1.
- No se ha certificado ningún artefacto original de predicción emitido en 2016 ni una edición GED17.1 disponible entonces.
- Por tanto, clasificar el supuesto pronóstico original como `RETROSPECTIVE_ONLY` / **no identificable como evaluación prospectiva**.
- Conservar la observación «transición 10» como **hecho codificado retrospectivo**, no como prueba de capacidad de predicción.

## Siguiente experimento falsable

Sobre todos los GWNO y años para los que existan dos ediciones sucesivas, construir una **matriz de revisiones de origen** (`0→0`, `0→1`, `1→0`, `1→1`) y, separadamente, una **matriz de revisiones del objetivo**. Cuantificar qué proporción de supuestos «fallos de transición» se explica solo por reclasificación del estado inicial. Congelar los denominadores reales, las ediciones y los SHA. Evitar extrapolar los resultados de Túnez al universo mundial sin efectuar ese análisis.

**Invariantes:** no alterar las 196 predicciones originales GEO2027 ni GEO2028, sus SHA, las sombras o las 15 alertas; no imputar resultados futuros ni presentar ediciones retrospectivas como datos disponibles en su año de cobertura.
