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
- [28/10/2026] Etapa 1 (revisión humana): encontré que la disponibilidad no valida el pasado y que faltan casos de prueba. Se pidió corrección (ver abajo).

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

**Hallazgos:**
- `consultar_disponibilidad` no validaba el inicio pasado pero `crear_reserva` sí, lo que contradice R7 y la consigna.
- Faltaban pruebas: cancelar repetida y consistencia entre disponibilidad y creación.
- Todos los errores son `ValueError`: limitación asumida por ahora.

