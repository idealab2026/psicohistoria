# Q-CANDIDATE: primer modelo retrospectivo de 30 y 90 días · protocolo anterior al cómputo

**Diseño fijado el 19-11-2026, antes de ejecutar los nuevos cálculos Q1→Q3.**

Este proyecto mide predicción **del indicador de registros UCDP Candidate**,
no probabilidades científicamente acreditadas de guerra real, y no sustituye
ni altera GEO2027, NEWCONF2027, ACD2027 ni GEO2028.

## Origen, horizonte y periodos

Tres años: 2024, 2025 y 2026. En cada año, **entrada** exclusivamente
UCDP Candidate acumulado enero–marzo, edición `YY.01.YY.03`. Filtrar eventos
estatales `type_of_violence=1`, precisión `date_prec <= 2`, con
`date_start >= 01/01` y `date_end <= 31/03`, sumando `best` por
`country_id`. Prohibir los eventos que cruzan el corte del trimestre.
El universo es **exactamente el listado fijo de 196 country_id** del documento
prospectivo GEO2027; se lee su universo, jamás se modifican probabilidades.

**Emisión hipotética de evaluación: 30 de abril** (NO está certificada la
disponibilidad real de las tres ediciones en esas fechas).
Se deja abril como mes no observado en el input para que el horizonte
evaluado sea posterior, sin utilizar abril para estimar las probabilidades.
**Ventanas exclusivas de emisión**:

- 30 días: 1–30 de mayo, ambos inclusive.
- 90 días: 1 de mayo–29 de julio, ambos inclusive.

**Outcome**: edición Candidate acumulada enero–septiembre del mismo año,
`YY.01.YY.09`, nunca la versión anual final. Para cada ventana, `y = 1`
si al sumar `best` de eventos tipo 1, precisión de fecha `date_prec <= 2`
y cuyo intervalo completo `[date_start,date_end]` esté contenido en la
ventana, resulta al menos **25 muertes registradas**; `y = 0` si no hay
ese registro en la edición Candidate para el país. El cero significa solo
**ausencia del umbral en esa versión**, no ausencia de violencia real.

No se adjudican a ninguna ventana eventos con fechas aproximadas o que
la atraviesen. Se registrarán recuentos de todos esos descartes. Esta
definición, más restrictiva que GED anual, constituye un **nuevo estimando**.

## Modelos inmutables y comparación

Entrenar/calibrar exclusivamente sobre **2024+2025** (392 país-años por
horizonte), evaluar **2026 como holdout temporal** (196 países, solo
una anualidad). Está prohibido reajustar la predicción 2026 después de
inspeccionar sus etiquetas; estas reglas se fijan antes de abrir la fuente.

Conservar tres modelos simples (todos se ajustan por horizonte usando
únicamente 2024 y 2025):

1. **Climatología global**: una probabilidad fija
   `(n_positivos+1)/(n_total+2)` para los 196 países.
2. **Persistencia binaria**: distinguir si el trimestre de origen tiene
   `best >= 25`. Probabilidad condicional suavizada hacia climatología
   con fuerza fija `k=10`:
   `(n_pos_grupo + 10*p_global)/(n_grupo+10)`.
3. **Volumen reciente por intervalos**: `best` de origen distribuido
   en cuatro categorías `0`, `1–24`, `25–99`, `>=100`. Misma
   fórmula de suavizado con `k=10`.

No hay hiperparámetros elegidos mirando 2026, optimización posterior
ni selección de «ganador» ex post. La evaluación 2026 reportará las tres
predicciones íntegramente.

## Métricas y reglas

Por horizonte y modelo: `Brier`, pérdida logarítmica, n positivos,
prevalencia observada, predicción media, ranking `precision@10`
(con desempate estable por country_id), Brier en países con origen
`best<25`. Comparar además el baseline determinista siempre-cero
en Brier, sin confundirlo con una probabilidad calibrada.
El ranking no es una recomendación ni un listado de nuevas guerras.

Publicar SHA-256 de los seis archivos originales, checks de duplicados,
fecha y tipo, número de eventos leídos, descartes temporales, países
ajenos al universo canónico y resultados agregados; publicar vector
2026 por país para reproducibilidad y con etiqueta
`RETROSPECTIVE_ONLY_NOT_ISSUED`.

## Resultado empírico ya ejecutado y congelado (holdout 2026)

Los seis archivos UCDP Candidate originales se descargaron y cotejaron por SHA-256. El
script `scripts/experiment_candidate_30_90_holdout.py` **aprendió solo de 2024–25**
y evaluó los 196 países de 2026 sin usar sus etiquetas durante el entrenamiento.
El informe reproducible en
[`data/candidate-30-90-baseline-holdout.json`](../data/candidate-30-90-baseline-holdout.json)
contiene las 196 filas, predicciones de los tres modelos, etiquetas retrospectivas,
fechas, métricas, parámetros y hashes completos. La CI rechaza cualquier desviación
respecto de los seis originales.

| Modelo | Brier 30d ↓ | Log-loss 30d ↓ | Brier 90d ↓ | Log-loss 90d ↓ |
|---|---:|---:|---:|---:|
| Climatología global | 0,07971365 | 0,29767164 | 0,11886799 | 0,40122975 |
| Persistencia binaria | 0,03919078 | **0,11322628** | **0,03141390** | 0,12629604 |
| Volumen previo, cuatro grupos | **0,03910474** | 0,11523153 | 0,03163051 | **0,10970295** |
| Referencia siempre cero (solo Brier) | 0,08673469 | — | 0,13775510 | — |

**Tasa observada en esta edición Candidate (NO de conflicto real):** 17/196
(8,67 %) a 30 días y 27/196 (13,78 %) a 90 días. El 2026 es un único año
de evaluación, con dependencia fuerte entre países. Los resultados pueden
cambiar si se usa otra edición o reglas distintas de precisión temporal.

**Concentración de la continuidad, no detección demostrada de onset:**

- Entre los **166 países** con menos de 25 muertes estatales registradas en
  Q1 de 2026, el horizonte 30d tiene **0 positivos**. Por definición, no hay
  en ese subconjunto nuevos casos que anticipar en esta cohorte.
- A 90d hay **solo 2 positivos de 166**, identificados como
  **Kenya** (Q1: 3; ventana posterior: 29) e **Indonesia**
  (Q1: 13; ventana posterior: 27). El modelo de volumen reciente
  les habría asignado `p≈0,14098`, y el binario de persistencia
  `p≈0,02141`. Son *registros Candidate* y no nuevos conflictos.
- La precisión retrospectiva entre las diez probabilidades mayores
  del modelo de volumen reciente es 9/10 a 30d y 10/10 a 90d, pero
  **domina la continuación** de episodios ya intensos. No mide
  habilidad para detectar países que antes estaban por debajo del umbral.
- El Brier en el subgrupo Q1<25 es 0,00020809 a 30d y 0,01118568 a
  90d con volumen reciente: los valores pequeños responden en buena
  parte al predominio de negativos, y a 30d **ninguna** escalada nueva
  ocurre dentro del subgrupo; no certificar onboarding de alertas.

**Integridad de los archivos:** la edición Q3 de cada año conserva el SHA
ya congelado en el estudio independiente Q2→Q3; los archivos Q1 tienen estos
nuevos hashes oficiales de bytes:

| Edición Q1 | SHA-256 |
|---|---|
| `24.01.24.03` | `ae794cc614a56a7445cdb72be95df7681431245c6ffda4ed6f3d56d36db29b6f` |
| `25.01.25.03` | `42465f8c081bd70e67221e216d2c0b3fae59586f1ca45561f48052a26a2910e8` |
| `26.01.26.03` | `a3cae550d6b806b3872aa4a12d0d47e2634ca2fc30dae385463230c659865346` |

**Incidencia de precisión temporal:** uno de los archivos originales incluye
`date_prec=0` en un evento estatal con gran valor de `best`.
Como esta codificación no se identifica con ninguno de los niveles 1–5
habituales descritos por UCDP, el auditor **la excluye y contabiliza**
como precisión temporal desconocida; jamás se transforma en `date_prec=1`
por conveniencia. La definición principal mantiene solo `date_prec∈{1,2}`.
Es imprescindible un análisis posterior de sensibilidad al tratamiento
de esa incertidumbre antes de aumentar la ambición del modelo.

**Lectura científica:** hay una señal descriptiva considerable para
*persistencia de intensidad de violencia organizada estatal registrada*,
pero **no hay todavía evidencia prospectiva** y el tamaño de muestra para
evaluar nuevas escaladas es insuficiente. Un único holdout temporal de un
año no certifica un sistema de alertas operativo.

**Reserva metodológica obligatoria:** la edición de marzo podría haberse
publicado después de la fecha de emisión hipotética; las URLs históricas
no demuestran cuándo apareció por primera vez cada archivo.
El resultado por tanto es una **prueba retrospectiva de señal con
vintages distintos**, no una validación as-of certificada, no un
backtest prospectivo y no una prueba de utilidad fuera de muestra en el
mundo real. Además, las fechas elegidas y los modelos responden a una
línea ya investigada históricamente; la selección no es ciega.
No hay intervalos de confianza creíbles con un único año de holdout
y dependencia entre países.

**Uso:** si ninguno supera de manera convincente la climatología y
la persistencia en 2026, no emitir alertas comerciales o públicas
basadas en esa familia. Si alguno mejora, exigir nuevas emisiones
inalterables y resolución futura para hablar de habilidad predictiva.
