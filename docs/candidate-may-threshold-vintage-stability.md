# Q-CANDIDATE · Estabilidad de cruces de umbral a 30 días entre ediciones (19-11-2026)

**Estudio suplementario POST HOC al hallazgo del umbral ≥5.** Su diseño queda fijado
antes de calcular las nuevas diferencias Q2→Q3 para umbrales 1/5/10.
Es una auditoría de fragilidad de etiquetas retrospectivas, no un nuevo modelo.

## Experimento y controles

Usar las **nueve fuentes oficiales Candidate Q1/Q2/Q3 de 2024, 2025 y 2026**
exactamente identificadas por los SHA-256 ya congelados en
`data/candidate-onset-label-revision-ties.json`. La cohorte Q1 será la de
196 países del registro GEO2027. El horizonte sigue siendo **1–30 mayo**
de cada año con estimando basado en eventos de violencia estatal
`type_of_violence=1`, `date_prec∈{1,2}`, completos dentro de la ventana
y fallecidos `best`. Los acumulados Q2 y Q3 se comparan para **exactamente
el mismo mes**, sin mezclar julio-septiembre.

Para T∈{1,5,10,25}, definir el conjunto de riesgo como países
`Q1_state_best<T`. En cada edición, el target es 1 si el total registrado
en mayo alcanza T y 0 si no consta en esa edición. Reportar, por año y T,
el tamaño del conjunto de riesgo, positivos Q2 y Q3, etiquetas adquiridas,
perdidas, y los códigos de país correspondientes. Medir asimismo la suma
absoluta de diferencias de fallecimientos `best` en los 196 países.
No confundir un cambio de etiqueta por revisión con un evento que
verdaderamente ocurrió o dejó de ocurrir.

En 2026, exigir que el Q1 y el Q3 reconstruidos sean idénticos al
`data/candidate-reactivation-threshold-grid.json` del PR #148
en las 196 filas, antes de comunicar ningún resultado. Para T=5
identificar expresamente si los dos casos observados a 30 días
sobreviven al cambio de versión. Si varía su estado, el resultado
«2/10 top alertas» deja de ser robusto incluso de modo retrospectivo.

**Límites:** las URLs archivadas no certifican fechas originales
de publicación; Candidate Q3 no es verdad final; solo 2024–2026
tienen aquí tres versiones trimestrales comparables. El contraste
del umbral 5 fue motivado por un resultado favorable ya observado,
por lo que es un análisis de sensibilidad **post selección**, nunca
una prueba independiente ni una puntuación prospectiva. No tocar
cohortes GEO2027/28 ni cambiar retrospectivamente el criterio.

**Fuentes:** <https://ucdp.uu.se/downloads/olddw.html>. Privacidad:
solo agregados institucionales y país, sin información personal,
fuentes de prensa ni registros de víctimas individuales.
