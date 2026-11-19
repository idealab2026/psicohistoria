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
