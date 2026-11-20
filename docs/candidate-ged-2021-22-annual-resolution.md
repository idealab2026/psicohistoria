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
