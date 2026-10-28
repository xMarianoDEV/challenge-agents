# Progreso y decisiones

## Entorno (datos reales, "no visible" si no se ve)
- Sistema operativo: Windows 10 22H2
- VS Code: 1.142.0
- Extensión GitHub Copilot Chat: 0.41
- Modelo seleccionado en Copilot Chat: Auto (GPT-6 Luna)
- Python: 3.12.6
- Dependencias externas: ninguna (solo biblioteca estándar)

## Registro cronológico
- [28/10/2026] Repo clonado. Decisiones: Python stdlib, zona UTC-3 fija, JSON, consola, rechazo de fechas pasadas con reloj inyectable.
- [28/10/2026] Etapa 1 (agente): dominio puro, data/inventario.json y 6 pruebas. El agente informó "Sin pendientes".
- [28/10/2026] Etapa 1 (revisión humana): encontré que la disponibilidad no valida el pasado y que faltan casos de prueba. Se pidió corrección.
- [28/10/2026] Etapa 1 (corrección): el agente unificó las validaciones en `_validar_solicitud` y agregó 3 pruebas nuevas más 2 casos en test_entradas_invalidas. Verifiqué con los tests (9 OK).
- [28/10/2026] Etapa 1 cerrada: verifiqué yo mismo 9 pruebas OK. Commits 050f840 (versión inicial del agente) y b195575 (corrección). SPEC.md actualizado con los nombres reales de pruebas y dos supuestos nuevos.
- [28/10/2026] Pendiente detectado en la revisión: ninguna prueba cubre un inicio igual al momento actual (debe aceptarse según SPEC). Se pide en la etapa 2.

## Etapa 1: dominio + pruebas

**Objetivo / requisitos:** R2, R3, R5, R6, R7 (dominio puro, sin archivos).

**Contexto dado al agente:** .github/copilot-instructions.md y SPEC.md, nombrados en el prompt; PROGRESS.md adjunto automáticamente como archivo abierto. Excluido: el PDF de la consigna.

**Permisos y controles:** modo Agent con "Manual permissions" (apruebo cada acción). Instrucción de no hacer commits; todos los commits los hago yo.

**Prompt (extracto):** "Implementá solo el dominio en reservas/dominio.py ... un único predicado de superposición ... reloj inyectable ... No hagas commits."

**Evidencia de uso de las instrucciones:** "Read copilot-instructions.md" visible. El archivo se nombró explícitamente en el prompt.

**Qué hizo el agente (informado por él):** creó reservas/dominio.py, data/inventario.json y tests/test_dominio.py (6 pruebas) y dijo haber ejecutado las pruebas con 6 OK.

**Qué verifiqué yo (ejecutado):**
- 28/10/2026, Python 3.12.6: `python -m unittest discover -s tests -v` → Ran 6 tests, OK.
- Leí dominio.py: predicado único en `se_superponen`, usado por la creación a través de `consultar_disponibilidad`; solo `activa` bloquea; cancelar conserva los datos; fechas sin offset rechazadas.
- Revisé test_entradas_invalidas: cubre unidad desconocida, solicitante vacío y de solo espacios, fecha inválida, sin offset, offset distinto, inicio > fin e inicio pasado. Faltaban inicio == fin y fecha de calendario inexistente.
- 28/10/2026, Python 3.12.6, tras la corrección: mismo comando → Ran 9 tests, OK.

**Hallazgos:**
- `consultar_disponibilidad` no validaba el inicio pasado pero `crear_reserva` sí, lo que contradice R7 y la consigna.
- Faltaban pruebas: cancelar repetida y consistencia entre disponibilidad y creación.
- Todos los errores son `ValueError`: limitación asumida por ahora.

**Corrección (28/10/2026):**
- Prompt (extracto): "Hacé que consultar_disponibilidad aplique las mismas validaciones que crear_reserva ... sin duplicar reglas; debe recibir el reloj inyectable."
- Qué cambió el agente: centralizó en `_validar_solicitud` la validación de unidad, intervalo e inicio futuro; disponibilidad recibe un reloj; agregó las pruebas solicitadas.
- Mi verificación: `python -m unittest discover -s tests -v` → Ran 9 tests, OK.

**Decisión humana:** aceptado con corrección.
**Motivo:** el dominio cumplía el predicado único, los estados y la cancelación, así que lo acepté. Corregí la disponibilidad porque la consigna exige que use las mismas reglas que la creación; sin la corrección, un horario pasado aparecía "disponible" y luego la creación lo rechazaba.
**Evidencia:** commit inicial 050f840, commit de corrección b195575, tests/test_dominio.py.