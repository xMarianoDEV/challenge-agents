import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from reservas.dominio import (
    ESTADO_ACTIVA,
    ESTADO_CANCELADA,
    cancelar_reserva,
    consultar_disponibilidad,
    crear_reserva,
)


INVENTARIO_PATH = Path(__file__).resolve().parents[1] / "data" / "inventario.json"
with INVENTARIO_PATH.open(encoding="utf-8") as archivo:
    INVENTARIO = json.load(archivo)

AHORA = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


class DominioReservasTests(unittest.TestCase):
    def crear(
        self,
        reservas=(),
        unidad="MIC-01",
        solicitante="Ana",
        inicio="2026-10-29T10:00:00-03:00",
        fin="2026-10-29T11:00:00-03:00",
        id_reserva="reserva-1",
    ):
        return crear_reserva(
            reservas,
            INVENTARIO,
            unidad,
            solicitante,
            inicio,
            fin,
            reloj=lambda: AHORA,
            generar_id=lambda: id_reserva,
        )

    def test_creacion_valida(self):
        reserva = self.crear()

        self.assertEqual(reserva.id, "reserva-1")
        self.assertEqual(reserva.unidad, "MIC-01")
        self.assertEqual(reserva.solicitante, "Ana")
        self.assertEqual(reserva.estado, ESTADO_ACTIVA)

    def test_rechazo_superposicion(self):
        existente = self.crear()

        with self.assertRaises(ValueError):
            self.crear(
                reservas=(existente,),
                inicio="2026-10-29T10:30:00-03:00",
                fin="2026-10-29T11:30:00-03:00",
                id_reserva="reserva-2",
            )

    def test_limites_consecutivos(self):
        existente = self.crear()

        siguiente = self.crear(
            reservas=(existente,),
            inicio="2026-10-29T11:00:00-03:00",
            fin="2026-10-29T12:00:00-03:00",
            id_reserva="reserva-2",
        )

        self.assertEqual(siguiente.estado, ESTADO_ACTIVA)

    def test_mic_02_simultanea(self):
        existente = self.crear()

        simultanea = self.crear(
            reservas=(existente,),
            unidad="MIC-02",
            id_reserva="reserva-2",
        )

        self.assertEqual(simultanea.unidad, "MIC-02")

    def test_entradas_invalidas(self):
        casos = (
            {"unidad": "NO-EXISTE"},
            {"solicitante": ""},
            {"solicitante": "   "},
            {"inicio": "fecha"},
            {"inicio": "2026-10-29T10:00:00"},
            {"inicio": "2026-10-29T10:00:00+00:00"},
            {
                "inicio": "2026-10-29T11:00:00-03:00",
                "fin": "2026-10-29T10:00:00-03:00",
            },
            {
                "inicio": "2026-10-28T08:59:00-03:00",
                "fin": "2026-10-28T10:00:00-03:00",
            },
        )
        for cambios in casos:
            with self.subTest(cambios=cambios):
                with self.assertRaises(ValueError):
                    self.crear(**cambios)

    def test_cancelacion_conserva_registro_y_libera_horario(self):
        existente = self.crear()
        reservas = (existente,)

        canceladas = cancelar_reserva(reservas, existente.id)

        self.assertEqual(len(canceladas), 1)
        self.assertEqual(canceladas[0].id, existente.id)
        self.assertEqual(canceladas[0].unidad, existente.unidad)
        self.assertEqual(canceladas[0].solicitante, existente.solicitante)
        self.assertEqual(canceladas[0].inicio, existente.inicio)
        self.assertEqual(canceladas[0].fin, existente.fin)
        self.assertEqual(canceladas[0].estado, ESTADO_CANCELADA)
        self.assertTrue(
            consultar_disponibilidad(
                canceladas,
                INVENTARIO,
                "MIC-01",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )
        )
        nueva = self.crear(reservas=canceladas, id_reserva="reserva-2")
        self.assertEqual(nueva.estado, ESTADO_ACTIVA)


if __name__ == "__main__":
    unittest.main()
