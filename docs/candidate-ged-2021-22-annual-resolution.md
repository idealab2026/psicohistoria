# PSICOHISTORIA · Candidate 2021/22 frente a GED anual · Protocolo 20-11-2026

**Diseño cerrado antes de inspeccionar los registros anuales de 2021/22.**
Ampliación independiente del estudio 2024/25 ya publicado (PR #151).
No emisión de nuevas probabilidades; no validación as-of ni score prospectivo.

## Fuentes, primero censo y SHA

Usar dos GED oficiales de primera edición anual correspondiente al año:
- **2021 → GED 22.1** original ZIP CSV, `https://ucdp.uu.se/downloads/ged/ged221-csv.zip`.
- **2022 → GED 23.1**, `https://ucdp.uu.se/downloads/ged/ged231-csv.zip`.

El catálogo histórico oficial UCDP documenta ambas ediciones:
<https://ucdp.uu.se/downloads/olddw.html>. Antes de calcular
los targets GED hay que descargar los **dos ZIP solo para censar sus nombres
de fichero, tamaño y SHA-256**; registrar ese censo en GitHub, congelar
cada SHA original en código y probar integridad de descargas futuras.
No usar GED actualizado 26.1 para resolver retrospectivamente 2021/22.

Candidate de cada año, exactamente dos ediciones acumuladas:
- `GEDEvent_v21_01_21_03.csv`, `GEDEvent_v21_01_21_09.csv`;
- `GEDEvent_v22_01_22_03.csv`, `GEDEvent_v22_01_22_09.csv`.

Sus URL/SHA/bytes ya fueron congelados en
`data/candidate-reactivation-threshold-grid.json`, anterior a la
comparación con GED. No cambiarlos ni sustituirlos por mensuales
revisados. **La comparación principal es Q3 frente a GED anual**,
sin Q2 para 2021/22, porque Q2 no se había congelado en el primer grid.

## Pregunta y poblaciones (idénticas a PR #151)

196 country_id fijos de GEO2027; origen Q1 enero–marzo `best` estatal
`type_of_violence=1`, `date_prec∈{1,2}`, evento completamente
dentro del trimestre. En cada umbral `T∈{1,5,10,25}`, población
a riesgo `q1_best<T`; no utilizar GED ni Q3 para fijarla.

Estimando **primario**: T=5 muertes estatales bien fechadas
en mayo **1–30**, objetivo `sum(best)>=5` bajo Candidate Q3
comparado con GED 22.1/23.1 para la **misma ventana**.

Secundarios congelados: T∈{1,10,25} a 30d y todos los
T∈{1,5,10,25} a 90d (mayo 1–julio 29).
Conservar la regla de intervalo completo: `date_start≥inicio`
y `date_end≤fin` sin prorrateo. `date_prec=0` se
excluye, junto a 3–5. Una ausencia de eventos suficientes
significa **que el umbral no figura en esa edición**, no ausencia
real de violencia.

## Salidas obligatorias

Por año/umbral/horizonte, `n_risk`, positivos Q3, positivos GED,
`both`, `candidate_only`, `ged_only`, `both_negative` y
denominadores de coincidencia. Nunca presentar porcentaje sin
su denominador, ni dividir cuando hay cero positivos.
Casos que pierden o ganan etiqueta con totales Candidate
y GED por país; estatutos `code_status` de los positivos
provisionales de mayo, sin identidades personales ni fichas
individuales. Conteo de IDs Candidate Q3 mayo que
coinciden exactamente con GED del mismo año:
cualquier tipo/ventana y mismo país+ventana. Un ID no
coincidente **no prueba** que el evento no ocurrió, fue recodificado,
dividido, fusionado o eliminado.

**Antifugas y control positivo obligatorios:**
- Comprobar los 2021/22 **8 grupos de riesgo y positivos Candidate**
  de 30/90d (4 umbrales × 2 horizontes) contra
  `data/candidate-reactivation-threshold-grid.json` del PR #148;
  si cambian, bloquear.
- Comprobar universo canónico y su SHA contra el mismo grid.
- GED 22.1 solo para 2021, GED 23.1 solo para 2022;
  filtrar `year` y verificar campos e ID únicos del año.
- No incluir violencia tipo2/3, fechas que cruzan el límite,
  `best<0`, `date_prec>2`, códigos de país fuera
  del universo o ZIP con SHA distinto.
- Limitar bytes comprimidos y descomprimidos, rechazar
  miembros ZIP inesperados o rutas inseguras.
- Controles sintéticos adversariales de parseo, fecha,
  versiones, SHA y división de evento; CI con replay exacto
  del JSON congelado. NINGÚN cambio en modelos originales.

## Síntesis conjunta (sin reetiquetado)

Sumar **únicamente** las tablas de confusión de 2021, 2022,
2024 y 2025 para comparar los cuatro años; mantener
la comparación 2024/25 de PR #151 inalterada y
referenciada por SHA/estructura. Reportar por separado
cada año para detectar cambios de cobertura.
No interpretar 4 anualidades como ensayos independientes
ni optimizar el umbral tras observar resultados.

**Límite estructural:** versiones GED y Candidate
tienen reglas de inclusión distintas, los GED anuales
siguen siendo revisables en ediciones posteriores,
y la fecha original de emisión de Candidate Q1
en cada año no está autenticada individualmente.
No se extrapola habilidad de forecast, no se
certifican eventos concretos ni se resuelve 2026
(su GED anual no está publicado). No alterar
GEO2027, NEWCONF2027, ACD2027 ni GEO2028.

Solo se usan fuentes públicas institucionales
y se citan sus versiones. Privacidad intacta.


## Resultados observados · censo previo SHA y evaluación separada

La primera ejecución de CI realizó **solo el censo original de ZIP**
(run [44773159865](https://github.com/idealab2026/psicohistoria/actions/runs/44773159865))
y dejó fijados los SHA antes del análisis de etiquetas:

| Año de eventos | Edición GED histórica | Archivo interno | ZIP (bytes) | SHA-256 ZIP |
|---|---|---|---:|---|
| 2021 | GED 22.1 | `GEDEvent_v22_1.csv` | 24.139.312 | `1741045a14a59e2ddbe9de4a190a7ef5b68d60d57be7e94178aff2e926a59f0d` |
| 2022 | GED 23.1 | `GEDEvent_v23_1.csv` | 26.587.114 | `9aa082f9e1f62da5ea3245c39b1cee45daab6dc8b3a17fb0f0cdae9ba13ce6f7` |

La evaluación posterior utilizó esos archivos y las cuatro ediciones Candidate
con SHA congelado desde el estudio anterior, sin sustituir fuentes ni
consultar la edición GED más moderna. El script comprobó que las **ocho**
combinaciones históricas de riesgo/positivos Candidate
(4 umbrales × 2 horizontes) por año coincidían con
`data/candidate-reactivation-threshold-grid.json`.

El [informe agregado y 392 vectores nuevos](../data/candidate-ged-2021-22-resolution.json)
conserva seis fuentes originales, referencias SHA, tasas, indicadores por país y
un **pooled** que incorpora literalmente los resultados de 2024/25
publicados en PR #151, sin volver a evaluarlos ni a calibrar modelos.

### Primario: países que partían de `Candidate Q1 best <5`, mayo 1–30

| Año | Población en riesgo | Candidate Q3 ≥5 | GED del primer corte anual ≥5 | Coincidentes |
|---|---:|---:|---:|---:|
| 2021 | 160 | 3 | 3 | **3** |
| 2022 | 161 | 1 | 1 | **1** |
| 2024 (PR #151) | 161 | 2 | 0 | **0** |
| 2025 (PR #151) | 160 | 4 | 1 | **1** |
| **Suma descriptiva** | **642 país-años** | **10** | **5** | **5** |

La **coincidencia de etiquetas positivas es 5/10** en cuatro anualidades.
Esta proporción no es una tasa estable de «confirmación»;
**2021–2022 retienen 4/4** y **2024–2025 solo 1/6**. No hay
casos GED-only a 30 días bajo T=5 entre estos 642 país-años,
pero otros T/horizontes sí introducen casos GED-only.
El tamaño 10 y la dependencia temporal/geopolítica descartan
interpretaciones de habilidad prospectiva o una probabilidad
universal de inclusión en GED.

Los tres casos 2021 son:
- **Perú:** Candidate Q3=16, GED22.1=16 (mayo 30d), `Clear`.
- **Turquía:** Candidate Q3=19, GED22.1=19, combinación `Clear`
  y `Check`; algunos IDs conservan cobertura del mismo año
  pero no exactamente la misma ventana.
- **Israel:** Candidate Q3=247, GED22.1=252,
  códigos `Clear`; el indicador no clasifica si este
  episodio constituye el inicio de un conflicto nuevo.
  
En 2022, **Togo**: Candidate Q3=8 y GED23.1=23,
con `Check deaths` en Candidate. Que un `Check` se mantenga
y un `Clear` pueda perder la etiqueta en 2024 (Bangladés)
refuta la heurística «`Clear` = definitivo, `Check` = incorrecto».

### Secundario: 90 días

| Año | Población en riesgo T=5 | Candidate Q3 ≥5 | GED anual ≥5 | Ambos | Solo Candidate | Solo GED |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 160 | 5 | 5 | 4 | 1 | 1 |
| 2022 | 161 | 8 | 2 | 2 | 6 | 0 |
| 2024 | 161 | 5 | 2 | 1 | 4 | 1 |
| 2025 | 160 | 7 | 3 | 3 | 4 | 0 |
| **Total** | **642** | **25** | **12** | **10** | **15** | **2** |

En 90 días la proporción de etiquetas positivas Candidate que
se mantienen en GED anual es **10/25 = 40 %**. No asumir que
la trayectoria de 30d (5/10) y la de 90d (10/25)
sean comparables como hipótesis independientes; los horizontes
se solapan. El resultado es muy sensible al año, criterio y
fuente de cierre. Mantener `T∈{1,5,10,25}`
por separado: la tabla principal no selecciona
un nuevo umbral tras observar el test.

### Control de identidad de eventos: no equiparar baja concordancia con desapariciones

| Año | IDs Candidate Q3 de mayo elegibles | ID existente en GED anual del mismo año | Mismo ID y misma ventana/país |
|---|---:|---:|---:|
| 2021 | 1.135 | 1.058 | 1.054 |
| 2022 | 752 | 715 | 711 |
| 2024 (PR #151) | 1.433 | 1.315 | 1.312 |
| 2025 (PR #151) | 1.545 | 1.412 | 1.404 |

En 2021–2022 **1.773 de los 1.887** IDs Candidate elegibles
de mayo están presentes de forma exacta en GED (94 % aprox.;
1.058+715 / 1.135+752). A pesar de ese solapamiento, algunas
**etiquetas nacionales de incidencia baja** cambian mucho.
No confundir match de ID con «verdad» o con inclusión causal
del mismo acontecimiento: es solo trazabilidad mecánica.

### Interpretación y siguiente decisión

La discordancia entre años **no** permite fijar una tasa universal
de revisión Candidate→GED ni seleccionar modelos con un único
bloque de años. Hay explicaciones potenciales que necesitan
prueba: modificaciones de criterios de inclusión,
composición de países/díadas próximos al umbral,
cambios de cobertura y revisión de estimaciones
de fallecidos. No se ha demostrado ninguna causa concreta;
la comparación aquí es descriptiva.

Próximo contraste más discriminativo: estratificar la
retención de etiquetas Candidate por `code_status` y
**distancia del total Candidate al umbral** (exactamente 5 frente
a muy por encima), y comprobar la estabilidad de los campos
de `year`, `type_of_violence`, fechas e IDs.
Solo con más casos (u objetivos menos raros) tiene sentido
considerar un modelo de incertidumbre de fuente.
El objetivo GED anual seguirá siendo distinto del
objetivo Candidate.

**No se emite pronóstico nuevo**, no se certifica
disponibilidad original as-of de Q1, no se resuelve GED 2026
ni se cambia ninguno de los 620 pronósticos preemitidos.
