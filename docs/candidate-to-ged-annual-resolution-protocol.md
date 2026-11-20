# PSICOHISTORIA · Resolución Candidate→GED anual · Protocolo 20-11-2026

**Diseño fijado ANTES de inspeccionar GED anual en esta investigación.** Es una auditoría retrospectiva de *estabilidad de un indicador*; no es una emisión predictiva ni un backtest `as-of` auténtico. El objetivo principal es refutar o sostener la fiabilidad de las etiquetas Candidate utilizadas en los estudios anteriores.

## Fuentes oficiales, sin equivalencias inventadas

- UCDP Candidate acumulado **2024 Q1/Q2/Q3** y **2025 Q1/Q2/Q3** (enero-marzo, enero-junio, enero-septiembre). La URL y SHA de los seis CSV se recuperan de `data/candidate-may-threshold-vintage-stability.json`, que conserva **ambos campos** por edición y cuya procedencia fue comprobada en el estudio anterior. La versión inicial del protocolo citaba otro registro que conserva los SHA pero no los URL; corregido antes de inspeccionar los resultados de GED, sin modificar datos ni estimando.
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

## Resultados auténticos del contraste anual (ejecutado 20-11-2026)

El programa descargó, verificó y procesó las dos ediciones GED anuales **sin reemplazar ninguna fuente provisional**, siempre con las seis ediciones Candidate Q1/Q2/Q3 2024–2025 de SHA fijos.

| Anualidad del evento | GED original / primer corte anual evaluado | SHA-256 ZIP original | Eventos del año observados en la edición GED |
|---|---|---|---:|
| 2024 | GED 25.1 / `GEDEvent_v25_1.csv` | `e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d` | 28.816 |
| 2025 | GED 26.1 / `GEDEvent_v26_1.csv` | `8c941d84954e555ee2e54f40fa04d9203bf1e2f962203d0a9930966c4947c667` | 25.770 |

Los SHA se fijaron en el script tras una **fase de censo de ZIP sin evaluar etiquetas**; el log de esa fase prueba la secuencia. Los ZIP fueron 29.307.888 y 39.122.522 bytes, respectivamente. Los originales GED completos **no se redistribuyen** desde el repositorio; la CI los descarga de UCDP y publica agregados con atribución. El informe congelado
[`data/candidate-to-annual-ged-resolution.json`](../data/candidate-to-annual-ged-resolution.json)
incluye 392 filas país-año, los SHA de los ocho archivos, los metadatos de parseo, matrices completas y los cambios de etiqueta por país.

### Hallazgo primario: ≥5 fallecimientos estatales registrados del 1 al 30 de mayo

El conjunto a riesgo se ha definido **únicamente con Candidate Q1**, sin fugas de la versión anual.

| Año | Países Q1 `best<5` | Candidate Q2 positivos | Candidate Q3 positivos | GED anual positivos | Positivos Q3 que GED conserva |
|---|---:|---:|---:|---:|---:|
| 2024 | 161 | 2 | 2 | **0** | 0 |
| 2025 | 160 | 5 | 4 | **1** | 1 |
| **Total descriptivo** | **321 país-años** | **7** | **6** | **1** | **1** |

La **coincidencia positiva entre Candidate Q3 y GED anual es 1 de 6**, un 16,7 % descriptivo para este *estimando muy específico, con muestra minúscula y años dependientes*. **No significa que el 83,3 % de los eventos originales sean falsos o inexistentes**. Los criterios Candidate/GED y la consolidación de actores/díadas difieren, y una única diferencia de cinco muertes puede cambiar la etiqueta binaria.

Cambios concretos principales:
- **2024:** Brasil (Candidate Q3=5, `check dyad`) y Bangladés (Candidate Q3=5, `clear`) pasan a 0 muertes estatales registradas según GED 25.1 **bajo estas reglas**. El hecho de que Bangladés figurase `clear` demuestra que ese código **no garantiza** estabilidad del indicador anual.
- **2025:** Ecuador (Candidate Q3=12, `check`), Brasil (7, `check dyad`) y Libia (7, `check dyad`) dejan de superar el umbral al cotejar GED 26.1. Laos figuraba positivo solamente en Candidate Q2 (5), pero ya había desaparecido de la etiqueta Candidate Q3.
- **2025 Indonesia:** Candidate Q3 registra **38** muertes en mayo y GED 26.1 **14** para el mismo país/mes; se conserva el positivo con T=5, **pero se pierde para T=25**. Los 38 de Candidate contienen 32 bajo `check deaths`, 4 `clear` y otras categorías de comprobación; el cambio del total no implica que desaparecieran exactamente 24 personas.

### Resultado secundario: 90 días (1 de mayo–29 de julio)

| Año | Riesgo T=5 | Candidate Q3 positivos | GED anual positivos | Ambos positivos | Solo Candidate | Solo GED |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 161 | 5 | 2 | 1 | 4 | 1 |
| 2025 | 160 | 7 | 3 | 3 | 4 | 0 |

También en 90 días las diferencias son importantes. No debe seleccionarse retrospectivamente el horizonte o umbral «ganador». El JSON contiene las matrices para T=1, 5, 10, 25 y ambos horizontes, incluyendo denominadores, nulos cuando no hay positivos y países con cambios.

### Comprobación para no confundir etiquetas con supervivencia de acontecimientos

En todos los eventos estatales Candidate Q3 con precisión 1/2 y fecha íntegramente dentro del 1–30 mayo, independientemente de su intensidad en Q1:

| Año | IDs Candidate Q3 elegibles | Mismo ID en GED del mismo año (cualquier tipo/fecha) | Mismo ID y misma ventana/país |
|---|---:|---:|---:|
| 2024 | 1.433 | 1.315 | 1.312 |
| 2025 | 1.545 | 1.412 | 1.404 |

Es decir, se observa una coincidencia exacta **del orden del 91 % de los identificadores** en el corte anual. Por tanto, **no es válido extrapolar la baja coincidencia de los indicadores binarios para los países subumbrales a una tasa de desaparición general de eventos Candidate**. Un ID que no coincide puede haberse eliminado, dividido, fusionado, recodificado o desplazado de fecha y país. El informe conserva ambas medidas por separado y no usa ID como sinónimo de «realidad».

### Interpretación científica y decisión

1. **El diseño de reactivación T=5 necesita cambiar de estado:** los buenos Brier retrospectivos frente a etiquetas Candidate provisionales **no demuestran** habilidad para anticipar el endpoint GED anual, y la tasa de correspondencia positiva es demasiado pequeña para vender una alerta.
2. **No recalcular el test para buscar una victoria:** publicar y conservar la comparación adversa, incluidos eventos `clear` que no alcanzan el indicador final, sin cambiar el umbral original.
3. **Distinguir dos familias de predicción:** *«superará T en Candidate bajo la edición mensual/trimestral»* y *«superará T en GED anual una vez consolidado»* son preguntas distintas. Los resultados históricos de la primera **no se transfieren** a la segunda.
4. **2026 todavía no está resuelto con GED anual:** los dos casos de Kenia y Libia de mayo de 2026 **permanecen sin resolución anual**, y el indicador Candidate `Clear-only` ya había mostrado fragilidad. No afirmar ni confirmación ni refutación de esos dos acontecimientos.
5. Una futura validación merece fuentes cuya **disponibilidad original pueda demostrarse**, más años, nuevos positivos, abstención explícita cuando los datos estén desactualizados y evaluación de alertas con coste operativo. Conservar todas las cohortes prospectivas congeladas sin modificación.

**Alcance:** UCDP GED anual tampoco es «verdad ontológica» inmutable; ediciones posteriores revisan registros. Las fechas de primera disponibilidad de las fuentes Candidate no están acreditadas y este experimento no es una validación prospectiva.
