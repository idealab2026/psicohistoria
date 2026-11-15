# Pre-registro científico GEO2028 · Horizonte tres años desde 2025

**Versión del protocolo: 15 de noviembre de 2026.** Este documento y el generador deben estar incorporados a la rama principal institucional **antes** del primer commit que publique las 196 probabilidades GEO2028. El código preparatorio no constituye una emisión. No existe aún ninguna etiqueta oficial de 2028.

## 1. Razón y alcance

La edición original verificada UCDP OrganizedViolenceCY 26.1 solo contiene datos hasta **2025**. No existe en este momento la edición anual final de **2026** necesaria para formular un GEO2028 con **horizonte 2026→2028 de dos años**. Prohibido simularla, retrotraer su fecha o afirmar que la emisión 2028 es una validación independiente del protocolo 2027.

En cambio, se puede pronosticar directamente **2025→2028 con horizonte de tres años**, sin utilizar datos posteriores a 2025. Se pre-registra esta opción como una cohorte prospectiva nueva para estudiar un horizonte temporal **distinto** y con **las mismas 196 unidades GWNO que GEO2027**. Los resultados futuros de 2027 y 2028 estarán correlacionados por países y origen; no podrán contarse como 392 pruebas independientes de superioridad.

**Variable binaria:** cualquier país del conjunto de 196 países con registro 2024 y 2025 de la fuente 26.1 tendrá etiqueta 1 si la primera edición oficial anual completa posterior a 2028 de UCDP OrganizedViolenceCY informa, en **2028**, al menos **25 muertes estatales organizadas** según el campo de muertes de la versión correspondiente. Si no existe un registro inequívoco para ese país-año, la etiqueta queda **sin resolver**, nunca 0 por defecto. No se confunde con la presencia de ACD o con un nuevo episodio de conflicto NEWCONF.

## 2. Modelo precomprometido y referencias

Se conserva **exactamente** la estimación original de las transiciones anuales de estado 0/1 de GEO2027, entrenada sobre la fuente 26.1 hasta 2025:

- Conteo global y por país de los pasos anuales 0→0, 0→1, 1→0 y 1→1.
- Probabilidad global por estado con suavizado Laplace Beta(1,1).
- Probabilidad por país de pasar al estado 1, con regularización de 20 observaciones equivalentes hacia la probabilidad global correspondiente.
- Con el estado 2025 s∈{0,1}, aplicar **tres**, no dos, veces el operador de transición a la probabilidad de estado activo. Para un vector de probabilidades anuales q=(q0,q1): p0=s y p_h=q0+(q1−q0)·p_(h−1), h=1,2,3.

**Primario:** probabilidad país Markov-3, campo p_model. **Comparador registrado:** modelo Markov-3 **global**, campo p_global_markov_3step. **Referencia primaria:** prevalencia global suavizada con Laplace sobre los mismos países 2021–2025, congelada con el origen 2025, campo p_baseline_global_5y. Esto evita ajustar o elegir una referencia a posteriori con resultados de 2028, aunque la referencia no incorpora el horizonte de tres años.

**Métrica principal futura:** diferencia Brier medio del modelo país menos referencia global de cinco años sobre el mismo conjunto completo de 196 países con etiqueta admisible de 2028. Informar además Brier del Markov global, log-loss y calibración por estado de origen 2025, sin declarar superioridad confirmatoria por una única cohorte. **Ningún cambio automático de modelo** después de ver resultados.

## 3. Prueba de continuidad exacta con las predicciones 2027

Antes de producir GEO2028, el generador deberá:

1. Verificar SHA-256 oficial de UCDP 26.1 y **todas las cinco emisiones 2027** originales, manifiestos y 424 preguntas país×endpoint emitidas con cero resultados.
2. Reproducir **byte a byte en cada uno de los 196 países** las probabilidades GEO2027 a dos pasos con la misma fuente de origen; cualquier discrepancia obliga a detener la nueva emisión.
3. Comparar los ID GWNO, estado 2025 y probabilidades 2027 con el primer compromiso GitHub. Calcular la tercera transición conservando el mismo kernel; almacenar p_issued_geo2027_2step_for_temporal_comparison_only en el nuevo documento exclusivamente para auditoría. **No reemitir ni editar** los archivos de 2027.
4. Rechazar cualquier dato de entrenamiento 2026, 2027 o 2028, etiquetas futuras, ID duplicados, probabilidades fuera de (0,1), horquillas que no sean de tres años, fuente sin hash verificado o denominador incompleto.

## 4. Dos hitos institucionales distintos

**Fase A — Antes de la emisión:** fusionar en main este documento, generador, tests y job de preparación; no hay pronóstico todavía. Esta separación hace verificable que la regla de modelización y la métrica principal existían antes de publicar los números.

**Fase B — Primera emisión:** crear nuevo commit público con el documento canónico completo GEO2028 de **196 países**, generado únicamente por el código y la fuente SHA-pinned; verificar la publicación en GitHub; registrar SHA-256 del documento, commit y fecha UTC real procedentes de GitHub en un manifiesto posterior, dejando la primera emisión intacta; auditar reproducibilidad en GitHub Actions. Se admitirá como emisión solo si la publicación fue anterior al 1 de enero de 2028 UTC. **Un timestamp de GitHub no es una notarización independiente**.

Si no se logra obtener o verificar la fuente oficial íntegra, la Fase B queda bloqueada; no se inventan predicciones ni se desactiva el control. No sustituir el próximo 2026→2028 horizonte dos años cuando se publique fuente de origen 2026: deberá definirse una **emisión separada**, igualmente antes de ver resultados.

## 5. Limitaciones científicas explícitas

Esta cohorte genera nuevas preguntas con resultado futuro genuinamente desconocido, pero **no añade un nuevo conjunto de países/orígenes**: GEO2027 y GEO2028 comparten 2025. Los modelos fueron elegidos después de inspeccionar datos históricos ya conocidos; por tanto el futuro es prospectivo, pero la superioridad, calibración y validez generalizable siguen sin demostrar. Un acierto para ambos años no equivale a dos réplicas independientes. Las tasas y resultados de ACD2027 y NEWCONF2027 son otros endpoints y no se mezclan.

No existe por ahora una fuente UCDP completa para resolver 2028 ni autorizamos cambios a las predicciones originales de GEO2027.
