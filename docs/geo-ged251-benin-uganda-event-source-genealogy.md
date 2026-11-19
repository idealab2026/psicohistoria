# PSICOHISTORIA · Benín y Uganda 2022: trazabilidad de cuatro eventos decisivos

**Diseño inicial 19/11/2026** (tras PR #137, antes de abrir las fuentes bibliográficas de los cuatro registros). Auditoría documental y de dependencia para dos parejas seleccionadas por impacto matemático en el umbral de 25 muertes de violencia estatal por país/año.

## Cohorte y pregunta

La revisión [#137](geo-ged251-near25-countryyear-census.md) fijó **392 país-años**, una banda inclusiva **15–35** muertes estatales GED25.1 y, antes de observar noticias individuales, estos pares candidatos:

| País-año | Total GED25.1 tipo 1 | Eventos seleccionados | Mortandad GED best por evento | Razón de prioridad |
|---|---:|---|---|---|
| Benín 2022 | 30 | 431254 / 431259 | 8 / 1 | Borrar *hipotéticamente* el primero da 22 |
| Uganda 2022 | 25 | 444764 / 444765 | 1 / 1 | Borrar *hipotéticamente* cualquiera da 24 |

Ambas parejas tienen coordenadas idénticas en el estudio anterior, pero **coincidencia geográfica no significa mismo incidente, misma víctima ni error**.

## Protocolo conservador

1. Volver a verificar SHA-256 del ZIP oficial UCDP GED25.1. Exigir identidad de cuatro IDs de evento, país, año, tipo de violencia y muertes best; abortar ante desviaciones.
2. Leer directamente los campos originales date_start, date_end, date_prec, where_prec, where_coordinates, where_description, event_clarity, dyad_name, side_a, side_b, source_original, number_of_sources y metadatos bibliográficos source_article, source_date, source_headline y source_office.
3. Establecer si UCDP reutiliza referencias bibliográficas entre los dos eventos. Conservar huellas SHA-256 de citas y un extracto corto de la referencia (no textos periodísticos). Distinguir noticia citada, fuente original alegada y **verificación independiente**.
4. Diferenciar fecha exacta y ventana incierta, y precisión espacial según [codebook oficial GED25.1](https://ucdp.uu.se/downloads/ged/ged251.pdf). where_prec=2 solo garantiza un margen aproximado de hasta 25 km; dos coordenadas idénticas podrían ocultar enfrentamientos diferentes. Un evento de claridad 2 puede agregar varios choques según codificación UCDP.
5. Buscar en fuentes públicas originales los episodios, establecer si los relatos identifican **fechas y víctimas distintas**, y clasificar cada pareja únicamente como _resuelta-distinta_, _solapamiento-verificado_ o _indeterminada_. La coincidencia en actor, díada, día o cifra no basta para declarar duplicación. Si falta material contrastable, mantener el estado de indeterminación.
6. No reescribir UCDP, emitir nuevas probabilidades GEO2027/2028 ni declarar cambio real en Brier. La sensibilidad 30→22 y 25→24 es **hipotética**, nunca una corrección certificada.

La evidencia de fuentes se recopila exclusivamente desde referencias públicas. No se incluyen nombres de particulares ni fuentes de la cuenta personal del investigador. Este protocolo está fijado en Git antes de analizar los metadatos de las cuatro entradas.

## Interpretación y reproducibilidad

La [metodología UCDP de claridad de evento](https://ucdp.uu.se/downloads/ged/ged251.pdf) distingue episodios claramente identificados (event_clarity=1) de agregados de varios enfrentamientos que el codificador no puede separar (=2). Esto es relevante para distinguir eventuales solapamientos **de la misma narración** de episodios que ocurren a unos días de distancia.

Ejecución:

- python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_benin_uganda_source_pair.py' -v
- python3 -B scripts/audit_geo_ged251_benin_uganda_source_pair.py --check-report
- python3 -B scripts/audit_public.py

La primera ejecución pública emitirá metadatos oficiales; se congelarán los resultados y el workflow pasará a replay exacto antes de fusionar. El informe no tiene estatus de validación externa mientras las noticias originales no hayan sido leídas y cotejadas por sus fechas y hechos.
