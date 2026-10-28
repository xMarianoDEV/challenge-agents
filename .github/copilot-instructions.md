# Instrucciones para el agente

Proyecto: app local de reservas de equipos de laboratorio en Python 3, SOLO biblioteca estándar.

## Reglas de trabajo
- No agregues dependencias externas (nada de pip install). Pruebas con `unittest`.
- La lógica de dominio (reservas/dominio.py) son funciones/clases puras: sin archivos, sin consola, y con reloj inyectable.
- Antes de dar una tarea por terminada, ejecutá `python -m unittest discover -s tests -v` y reportá la salida real. Si no lo ejecutaste, decilo.
- NO hagas commits ni push. Los commits los hace el humano.
- NO inventes resultados de pruebas, versiones ni comandos que no ejecutaste.
- Al terminar cada etapa, agregá una entrada breve en PROGRESS.md (qué hiciste, qué ejecutaste, qué quedó pendiente).
- No agregues funciones fuera de alcance (login, roles, notificaciones, administración del inventario).

## Reglas de dominio (adaptación específica)
- Intervalo semiabierto [inicio, fin): 10:00-11:00 y 11:00-12:00 de la misma unidad NO se superponen.
- Predicado de superposición: `inicio_a < fin_b and inicio_b < fin_a`. Existe en un único lugar y lo usan tanto la creación como la consulta de disponibilidad.
- Solo las reservas con estado `activa` ocupan el intervalo. Las `cancelada` no bloquean.
- Cancelar nunca borra: conserva id y datos, y cambia el estado a `cancelada`.
- Zona horaria UTC-3 fija; fechas ISO 8601 con offset. Fechas sin offset se rechazan.
- Se rechazan reservas con inicio en el pasado (según el reloj inyectado).

## Inventario fijo
MIC-01 y MIC-02 (microscopio digital), OSC-01 (osciloscopio), MUL-01 (multímetro), FUE-01 (fuente de alimentación).