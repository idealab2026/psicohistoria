# PSICOHISTORIA · Resolución Candidate→GED anual · Protocolo 20-11-2026

**Diseño fijado ANTES de inspeccionar GED anual en esta investigación.** Es una auditoría retrospectiva de *estabilidad de un indicador*; no es una emisión predictiva ni un backtest `as-of` auténtico. El objetivo principal es refutar o sostener la fiabilidad de las etiquetas Candidate utilizadas en los estudios anteriores.

## Fuentes oficiales, sin equivalencias inventadas

- UCDP Candidate acumulado **2024 Q1/Q2/Q3** y **2025 Q1/Q2/Q3** (enero-marzo, enero-junio, enero-septiembre). El URL y SHA de los seis CSV deberán ser los ya congelados en `data/candidate-onset-label-revision-ties.json`.
- **GED Global 25.1** (primera versión anual con información de **2024**) a partir del ZIP original `https://ucdp.uu.se/downloads/ged/ged251-csv.zip`.
- **GED Global 26.1** (versión anual que incluye **2025**) a partir de `https://ucdp.uu.se/downloads/ged/ged261-csv.zip`. GED 26.1 puede revisar también 2024, pero **la comparación principal 2024 se resolverá con 25.1**, evitando elegir GED posterior por conveniencia.
- Los dos ZIP se descargarán primero para **censar nombres de miembros, formato y SHA-256 sin calcular ninguna etiqueta**. Sus SHA se fijarán explícitamente en el código **antes** de la evaluación. Todo cambio posterior de bytes debe bloquear el cómputo.
- Universo fijo de los 196 códigos `country_id` GEO2027, cuya fuente en `data/forecast-2027-ucdp261.json` debe conservar su SHA original de estudios ya publicados. No alterar las cohortes ni probabilidades emitidas.
- Fuentes y atribución: <https://ucdp.uu.se/downloads/> y <https://ucdp.uu.se/downloads/olddw.html>. UCDP permite reutilización con atribución CC BY 4.0.

## Estimando primario congelado antes de medir

**Países en riesgo:** `Candidate Q1, type_of_violence=1, date_prec∈{1,2}, best Jan1-Mar31 < 5`.

**Ventana fija de 30 días:** del **1 al 30 de mayo** de 2024 y 2025. Para cada país y fuente por separado, `y=1` si la suma `best >= 5` de eventos con:
- `type_of_violence=1`;
- `date_prec∈{1,2}`;
- intervalo `[date_start, date_end]` **íntegramente** contenido en 1–30 de mayo;
- mismo `country_id` del universo;
- `best` válido y no negativo.

**Etiquetas comparadas** de la **misma ventana**: Candidate Q2, Candidate Q3 y GED anual 25.1 (2024) / 26.1 (2025). Cero significa solo *que esa edición no contiene registros suficientes bajo este indicador*, no ausencia de violencia real. GED anual sigue siendo una edición revisable en años posteriores.

**Secundarios prefijados:** umbrales `T∈{1,10,25}` en 30 días y `T∈{1,5,10,25}` para **90 días** (1 mayo–29 julio), con población a riesgo `Candidate Q1 best<T` recalculada por cada umbral; comparar Candidate Q3 contra GED anual. 90 días Q2 no es válido porque julio no está cubierto por Q2.

El análisis no elegirá el umbral/horizonte ganador después de medir resultados. El caso T=5 a 30 días es **hipótesis postselección** del trabajo anterior, no evaluación ciega.

## Estadísticos obligatorios

Para cada año, ventana, umbral y versión provisional comparada con GED anual:
- `n_at_risk`, `candidate_positive`, `ged_positive`, `both_positive`, `candidate_only`, `ged_only`, `both_negative`, `disagreements`.
- `candidate_positive_matching_ged_share` = both/candidate_positive, **nulo cuando denominador 0**; `candidate_sensitivity_to_ged_label` = both/ged_positive, también nulo cuando denominador 0. *No llamarlos exactitud del mundo real.*
- Códigos de países con cambio de etiqueta y sus totales provisionales y anuales, especialmente para T=5/30d. Los porcentajes con n muy pequeños se interpretarán solo descriptivamente.
- Recuento de eventos Candidate Q3 que cumplen el filtro mayo y cuyos **IDs** están presentes en GED anual: `matched_id_annual_any_window_or_type` y `matched_id_same_country_and_window` para distinguir movilidad/codificación. Los ID son auxiliares, no verdad sobre supervivencia de episodios: recodificación y división/fusión de acontecimientos invalidan una equivalencia estricta ID↔evento.
- Para países provisionalmente positivos T=5/30d, sumar `best` por grupos `code_status` en Candidate Q3 y contraste GED nacional. `Clear` NO es garantía de que un caso se mantendrá y `Check dyad` NO prueba que sea falso.

## Controles antivicio metodológico y de integridad

1. **Origen temporal:** no usar GED final ni Candidate Q2/Q3 para determinar quién está a riesgo. La fuente de riesgo solo es Candidate Q1 y se compara por SHA.
2. **Anualidad estricta:** ZIP GED 25.1 solo se utiliza para 2024; ZIP GED 26.1 solo para 2025. Filtrar la columna `year` antes de atribuir eventos.
3. **Parseo conservador:** CSV original completo, ID no vacío y único en año objetivo, tipo/país/fecha/precisión y `best` válidos. `date_prec=0` queda fuera del indicador. No recortar ni prorratear eventos que atraviesan ventanas.
4. **Trazabilidad**: registrar SHA-256, bytes ZIP originales, miembro CSV preciso, conteo de filas, exclusiones de categoría/precisión/ventana y datos agregados nacionales. Si cambia un archivo, **fail-closed**.
5. **Reproducción:** CI debe descargar los 8 originales y recomputar exactamente el JSON congelado. Pruebas sintéticas adversariales de cambio de país, tipo, ID, fecha, ZIP alterado y división de evento.
6. **Privacidad:** proyecto exclusivamente institucional; sin datos privados, sin textos de noticias ni fichas de víctimas.
7. No alterar predicciones fijas **GEO2027/NEWCONF2027/ACD2027/GEO2028** ni presentar GED 2024/25 como emisión prospectiva. No atribuir fechas de primera publicación sin un comprobante archivístico independiente.

## Interpretación predefinida

Si la mayor parte de candidatos T=5 desaparece bajo GED anual, **la habilidad retrospectiva frente a Candidate no puede extrapolarse al indicador GED**; exigir redefinición explícita de target y volver a evaluar desde cero, no retocar modelos mirando el test. Si los positivos permanecen, solo podemos afirmar *estabilidad histórica en esas dos anualidades bajo esas versiones*, sin validar 2026 ni su capacidad de anticipar futuros cambios geopolíticos.

**No declarar confirmados los dos casos Kenia/Libia de mayo de 2026:** GED anual definitivo de 2026 no está aún disponible. Este estudio resuelve 2024–2025 y mide la posible fragilidad de la familia de objetivos.
