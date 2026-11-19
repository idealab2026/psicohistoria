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
