# PSICOHISTORIA · Censo de país-años cercanos al umbral de 25 fallecidos

**Diseño fijado 19/11/2026 antes de obtener los resultados de este censo.** Extensión motivada por el hallazgo de la [PR #136](geo-ged251-candidate-source-threshold-triage.md): los nueve países-año previamente investigados acumulan muchos más de 25 fallecidos, por lo que no son útiles para detectar fragilidad de ese umbral.

## Pregunta científica

¿En cuántos país-años cercanos a 25 muertes de violencia de base estatal una hipotética eliminación de un evento de GED25.1 cambiaría la etiqueta binaria, y entre esos casos aparecen además candidatos por proximidad espacial/temporal?

La pregunta **no implica que los eventos sean duplicados ni que deban eliminarse**. Se estudia sensibilidad matemática de la etiqueta, no corrección de UCDP.

## Contrato del censo antes de extraerlo

- Población cerrada: **196 GWNO de las predicciones GEO2027**, años **2021 y 2022** (392 país-años).
- Datos: [archivo oficial GED25.1](https://ucdp.uu.se/downloads/ged/ged251-csv.zip), hash SHA-256 idéntico al usado en #135 y #136: e256f1fb20a579d8b2f910e5bae212f486d3002adaa2e4359ace740c737da05d.
- Medición: sumar **best** para todas las filas de tipo 1 (state-based) de un mismo GWNO/año, **incluidas las no geocodificables**; sin filas equivale a total cero *en la base*, no a ausencia histórica probada.
- **Banda marginal predeterminada 15–35, inclusiva**, equivalente a diez fallecidos por debajo y por encima de 25. No ajustar el intervalo tras observar resultados.
- Cada país-año marginal se presenta con total, actividad binaria ≥25, número de filas estatales, número de filas con coordenadas/intervalos elegibles y número de registros individualmente *pivote*: para T≥25, eliminar una sola fila de best=b dejaría T−b menor de 25.
- Buscar pares de eventos del **mismo GWNO/año**, a ≤25 km y con separación de intervalos ≤3 días, independientemente de su díada. Registrar candidatos y si cualquiera de las dos hipotéticas eliminaciones individuales cruza el umbral. Coordenadas iguales NO son confirmación de identidad.
- Fuera de esta banda se muestran solo conteos agregados: total cero registrado, positivo menor que 15, 15–24, 25–35 y mayor de 35. Los casos de total cero nunca se interpretan como observación exhaustiva de ausencia de violencia real.
- Se preserva el vector emitido GEO2027, GEO2028 y la cadena previa de Burundi. No se revisan fuentes humanas, no se recodifican etiquetas y no se calcula una mejora predictiva.

El interés es **priorizar futuras verificaciones**: un par próximo potencialmente pivote importa más a la definición de GEO que uno localizado en un país con decenas de miles de víctimas. Pero aun si una eliminación hipotética cruza el umbral, la acción está prohibida hasta contar con evidencia independiente, adjudicación documental y protocolo de revisión de etiquetas.

## Reproducibilidad

1. python3 -B -m unittest discover -s scripts -p 'test_audit_geo_ged251_near25_countryyear_census.py' -v
2. python3 -B scripts/audit_geo_ged251_near25_countryyear_census.py --check-report
3. python3 -B scripts/audit_public.py

La primera ejecución emitirá resultados sobre el ZIP oficial, se congelarán en un JSON verificable y el workflow pasará a comparación exacta. Esta es una **investigación histórica**, no una predicción realizada en 2021/2022 ni una tasa de error global de UCDP.

Referencia: [UCDP metodología GED](https://www.uu.se/en/department/peace-and-conflict-research/research/ucdp/ucdp-methodology.html).

## Resultados oficiales reproducidos desde GED25.1

Se han evaluado los **392 países-año** de la cohorte de **196 GWNO × 2021–2022** y el **ZIP oficial GED25.1** fijado por SHA-256, sin leer probabilidades prospectivas para seleccionar casos.

| Rango de muertos estatales registrados (best) | Países-año |
|---|---:|
| 0 en GED25.1 (no prueba ausencia real) | 293 |
| 1–14 | 22 |
| **15–24** | **8** |
| **25–35** | **6** |
| ≥36 | 63 |
| **Total** | **392** |

De los **14 países-año** de la banda preseleccionada 15–35, **5** contienen al menos una fila GED cuya eliminación hipotética aislada cambiaría el estado anual; en total son **13 filas potencialmente pivote**. La búsqueda espacio-temporal encuentra **15 pares cercanos**, de los que **2** incluyen un extremo cuya supresión hipotética cruzaría el umbral.

### Prioridades documentales propuestas

| País-año | Muertes estatales GED25.1 (best) | IDs GED próximos | Muertes individuales del par | Gap entre fechas | Distancia | Sensibilidad |
|---|---:|---|---|---:|---:|---|
| **Benín 2022** | 30 | 431254 / 431259 | 8 / 1 | 2 días | 0 km | Solo eliminar el evento con 8 fallecidos cambiaría el estado 30→22 |
| **Uganda 2022** | 25 | 444764 / 444765 | 1 / 1 | 3 días | 0 km | Cualquiera de las dos eliminaciones individuales cambiaría 25→24 |

**No son duplicaciones verificadas.** En ambos pares las coordenadas coinciden exactamente y los niveles de precisión UCDP son 2/2 para Benín y 1/1 para Uganda. Esto aumenta el interés de la revisión de fuentes, pero el mismo lugar puede sufrir enfrentamientos diferentes incluso con los mismos actores. En Uganda, dos eventos codificados en días separados pueden ser legítimos.

Estos pares se deben contrastar con documentos, partes locales, actores, víctimas y genealogía de las fuentes **antes de concluir cualquier error de medición**. Incluso si se demostrase una duplicación, habría que verificar las reglas UCDP de inclusión de dyadas/país-año y la compatibilidad con el objetivo de las predicciones emitidas. No editar automáticamente la serie.

### Otros registros hipotéticamente decisivos

Además de Benín y Uganda, en la banda marginal hay casos con posibilidad de cambiar la etiqueta mediante una única supresión *aunque no tengan un par cercano con el filtro fijado*: **Azerbaiyán 2021** (30 muertes; 2 filas pivote), **Togo 2022** (34; 1 fila pivote) y **Sudán 2021** (31; 3 filas pivote). Son sensibilidades aritméticas, no investigaciones documentales realizadas.

El resultado respalda **priorizar auditorías de fuentes alrededor del umbral**, pero no establece cuántos errores existen en UCDP ni si el modelo GEO anticipa mejor los años futuros. Las revisiones de datos potenciales son retrospectivas y no modifican ninguna predicción ya emitida.

Fuente reproducible: [JSON del censo near25 con 14 país-años](../data/geo-ged251-near25-2021-22-countryyear-census.json). El pipeline debe exigir ahora comparación exacta del JSON congelado.
