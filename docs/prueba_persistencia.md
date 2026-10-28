# Prueba manual de persistencia tras reiniciar

Ejecutar cada comando desde la raíz del repositorio. Cada invocación inicia un
proceso nuevo de Python y usa `data/reservas.json`; el archivo no debe borrarse
entre comandos. El intervalo de prueba es futuro para evitar depender del reloj.

Antes de empezar, `data/reservas.json` no debe existir, así el primer ID es `RES-001`.

| Paso | Comando | Resultado esperado | Observado |
|---|---|---|---|
| 1. Crear reserva | `python -m reservas.cli reservar MIC-01 "Prueba persistencia" 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00` | Imprime `Reserva creada: RES-001`. | `Reserva creada: RES-001` |
| 2. Comprobar creación | `python -m reservas.cli listar` | Aparece la reserva con unidad `MIC-01`, solicitante `Prueba persistencia` y estado `activa`. | `RES-001 MIC-01 Prueba persistencia 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00 activa` |
| 3. Cerrar la terminal, abrir otra, entrar a la raíz del repo y comprobar (reinicio 1) | `python -m reservas.cli listar` | La reserva sigue en la lista con sus datos y estado `activa`. | `RES-001 MIC-01 Prueba persistencia 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00 activa` |
| 4. Cancelar la reserva | `python -m reservas.cli cancelar RES-001` | Imprime `RES-001 cancelada`. | `RES-001 cancelada` |
| 5. Cerrar la terminal, abrir otra, entrar a la raíz del repo y comprobar (reinicio 2) | `python -m reservas.cli listar` | La reserva sigue en la lista, conserva sus datos y aparece con estado `cancelada`. | `RES-001 MIC-01 Prueba persistencia 2099-11-03T10:00:00-03:00 2099-11-03T11:00:00-03:00 cancelada` |

**Fecha de ejecución:** 28/10/2026. Python 3.12.6. Se partió de un `data/reservas.json` borrado antes del paso 1. Se cerró la terminal y se abrió una nueva entre los pasos 2 y 3, y entre los pasos 4 y 5.
**Resultado:** coincide con lo esperado: la reserva activa y la cancelada sobrevivieron a un reinicio cada una, con id y datos intactos.