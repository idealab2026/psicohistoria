# NEWCONF-2027 · Diagnóstico de información prospectiva (11-11-2026)

**Estudio adicional antes de resultados, no cambia la predicción emitida.** Fuente: `data/forecast-2027-newconf.json`, emisión 11-11-2026, 196 países, `forecast_id=PSICO-QGEO01-NEWCONF2027-ORIGIN2025-V1`. Reproducción: `python3 scripts/diagnose_newconf2027_event_count.py`.

## Distribución implícita de número de países con nuevos conflictos

Se calcula la distribución **Poisson-binomial exacta** de la suma de 196 indicadores Bernoulli con las `p_model` congeladas. **Hipótesis adicional fuerte:** independencia condicional de los eventos entre países. La guerra regional, contagios y shocks comunes pueden invalidarla; **no** se presenta como intervalo de cobertura calibrada empíricamente.

- Esperanza: **2,490944756** países; varianza: **2,388848984**; rango de cuantiles centrales 2,5–97,5 % bajo la hipótesis: **0–6**.
- Probabilidad modelizada de **0** países: **7,85 %**; de **0 o 1**: **28,27 %**; de **0, 1 o 2**: **54,36 %**.
- Probabilidad de **6 o más**: **3,80 %**.
- Las 196 filas contienen **12 probabilidades distintas**: los empates hacen engañosas las clasificaciones top-k sin intervalos de desempate.
- En los 20 países de probabilidad más alta, el modelo espera **1,16486** eventos; es una expectativa matemática, no un número observado ni un pronóstico de acierto top-20.

## Consecuencia científica

Que ocurran cero, uno o dos conflictos **no refuta por sí solo** el modelo: esas realizaciones acumulan ~54,36 % de probabilidad bajo sus propias hipótesis. Pero tampoco confirma el modelo que ocurra una cifra esperada. La evaluación que discriminan Brier/log-loss frente al baseline y la calibración **solo puede realizarse con outcomes oficiales genuinos**, siguiendo `docs/newconf-2027-evaluation-contract.md`.

El escaso número de eventos puede volver anchos e inestables los intervalos de diferencia de Brier. No se puede convertir la validación futura de una sola cohorte en una afirmación causal o de superioridad generalizable. **Esta nota es una prueba de poder informativo/fragilidad, no un backtest ni una certificación de skill.**

## Integridad

Este diagnóstico únicamente lee la emisión original. No escribe `data/forecast-2027-newconf.json`, no cambia el protocolo ni el comparador preregistrado, no introduce outcomes de 2027 y no usa información posterior a la emisión. Los porcentajes se redondean para lectura.
