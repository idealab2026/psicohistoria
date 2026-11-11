# NEWCONF-2027 · Contrato de resolución oficial v1

**Fecha del contrato: 11-11-2026. Estado: preparado, sin etiquetas ni resultados de 2027.**

Este documento implementa la futura evaluación de la emisión [NEWCONF-2027](../data/forecast-2027-newconf-manifest.json). **No modifica el protocolo preregistrado** `docs/newconf-2027-protocol.md`, el código generador, el documento de 196 probabilidades ni la referencia original GEO-2027.

## 1. Identidad de las observaciones

El objetivo congelado es `ANY(newconf=1)` de la variante **UCDP Intrastate Country Level Multiple Onset** en el año calendario **2027**, por país de gobierno Gleditsch–Ward. `newconf` no se puede sustituir por `onset1`, `onset2`, una cifra de muertes, actividad en guerra o por observaciones de otra variante de UCDP.

Un país-año puede aparecer varias veces en el CSV de episodios de Multiple Onset. Para el mismo `(gwno_a,year=2027)`, el valor binario es el **OR de todas las filas `newconf`**. Se conservan contadores de filas de episodio, claves duplicadas, grupos únicos, valores positivos por país y episodios positivos. Ninguna fila extra incrementa el denominador del Brier.

Si falta una fila para un país del conjunto emitido, o una fila tiene `newconf` vacío, **ese país permanece no resuelto**. No se aplica `fillna(0)`, no se usa un registro de 2026 o de 2028 para imputarlo, y no se eliminan países de la cohorte original.

## 2. Fuentes y procedencia

El evaluador `scripts/evaluate_2027_newconf_official.py` solo admite:

- un CSV descargado directamente de un enlace literal HTTPS `https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-XXX.csv`, donde la edición debe ser **281 o posterior**;
- el SHA-256 exacto de **los bytes del CSV** recibido; se rechazan cambios, URL alternativas y subdominios sospechosos;
- una fecha declarada de publicación ISO posterior al **31-12-2027**.

La URL, la fecha y el hash proporcionados por un operador **no certifican** que sean la **primera edición completa** UCDP que cubre 2027. El informe siempre indica `first_complete_official_2027_release_independently_attested=false` y `future_predictive_skill_independently_verified=false`. Solo una verificación institucional documental independiente podrá resolver ese requisito de procedencia. **No publicar una afirmación de skill solo porque existan puntuaciones numéricas.**

Estado actual del catálogo UCDP en 11-11-2026: versión de Onset **25.1** (hasta 2024); no hay resultados elegibles de 2027.

## 3. Denominador y evaluación

El archivo prospectivo original tiene **196 países** y es inmutable: SHA-256 `e4482da7396872645d5101115435143d98fd9fdb1db1b1fdf41a42c99fc04b74`, primer commit público `f3f2c17c9d4f5dd56266e376cd2d765f33f3dd97` (2026-11-11 10:10:21 UTC), generador SHA-256 `353508031023a16f901b61c80d23f6ee83af29e80745a757011881f0dc8c2d14`. Se auditan los tres ficheros antes de puntuar.

- Con **menos de 187 países resueltos de 196**, el informe presenta solo cobertura y positivos observados entre los resueltos. **No** calcula scores, intervalos ni rankings.
- Con **187–195 resueltos**, se permiten **métricas exploratorias** en esa misma muestra, con países ausentes explícitos. No se presenta rendimiento para la cohorte completa y se omiten todas las alertas top-k.
- Solo con **196/196 resueltos**, se permite el análisis de alertas top 5, 10 y 20 con protección contra empates. Si el valor de corte coincide entre múltiples países, el número de aciertos se informa como **intervalo mínimo–máximo** entre todos los desempates admisibles, nunca como ordenación arbitraria de identificadores.
- La fuente puede incluir países nuevos fuera del conjunto de emisión: se informan como ignorados y **no** se altera la cohorte original.

**Loss primaria**: diferencia `Brier(modelo) - Brier(referencia global 2020–2024)` en el mismo conjunto resuelto. Scores secundarios: Brier y log-loss para `p_model`, `p_baseline_global_5y`, `p_country_eb` y `p_activity_global`; la referencia `no-newconf` solo tiene Brier definido. Intervalo bootstrap del delta de Brier con **2.000 remuestreos por país** (una unidad país-año por país); este intervalo no capta shocks comunes ni elimina el problema de muy pocos eventos. Calibración por intervalos fijos `[0,.01), [.01,.025), [.025,.05), [.05,.1), [.1,1)`.

## 4. Ejecución cuando exista realmente una edición oficial

El comando siguiente es un **ejemplo futuro, no ejecutarlo ahora como evaluación real**. La ruta, el enlace, el SHA y la fecha deben sustituirse por datos **verificados**, no inventados:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/evaluate_2027_newconf_official.py \
  --official-csv /ruta/a/archivo_2027_original.csv \
  --official-url "https://ucdp.uu.se/downloads/onset/ucdp-intrastate-country-multiple-onset-XXX.csv" \
  --official-sha256 "<SHA-256_REAL_DEL_ARCHIVO>" \
  --release-date "AAAA-MM-DD" \
  --output /tmp/newconf_2027_candidate.json
```

El fichero de salida es un **candidato de resolución**, no una certificación automática ni un sustituto del original. El evaluador no descarga un archivo no suministrado, no altera probabilidades, no modifica el manifiesto, no guarda resultados sintéticos como datos reales y no envía notificaciones. Las pruebas `scripts/test_evaluate_2027_newconf_official.py` utilizan exclusivamente muestras sintéticas y la emisión original para verificar integridad.

## 5. Condición de cierre científico

El expediente [issue #45](https://github.com/idealab2026/psicohistoria/issues/45) debe permanecer abierto hasta que se confirme documentalmente una primera edición completa con etiquetas 2027, se resuelva el denominador y se publique tanto el rendimiento del modelo como el de los comparadores sin selección posterior de ganador. Se deben comunicar también resultados nulos y negativos. No se permiten futuros cambios retroactivos al primer documento emitido ni al modelo elegido.

**Estado al cerrar este desarrollo técnico:** evaluador preparado y probado, **0 outcomes 2027 disponibles, 0 skill demostrada**.
