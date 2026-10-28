import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from reservas.dominio import ESTADO_ACTIVA, ESTADO_CANCELADA
from reservas.repositorio import RepositorioReservas


INVENTARIO = {
    "MIC-01": "Microscopio digital",
    "MIC-02": "Microscopio digital",
}
AHORA = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


class RepositorioReservasTests(unittest.TestCase):
    def crear_repositorio(self, ruta):
        return RepositorioReservas(
            ruta,
            inventario=INVENTARIO,
            reloj=lambda: AHORA,
        )

    def test_persiste_reservas_y_continua_secuencia_tras_reiniciar(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "reservas.json"
            repositorio = self.crear_repositorio(ruta)

            primera = repositorio.crear(
                "MIC-01",
                "Ana",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )
            segunda = repositorio.crear(
                "MIC-02",
                "Luis",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )
            repositorio.cancelar(primera.id)

            reiniciado = self.crear_repositorio(ruta)
            reservas = reiniciado.listar()

            self.assertEqual(
                [reserva.id for reserva in reservas],
                ["RES-001", "RES-002"],
            )
            self.assertEqual(reservas[0].estado, ESTADO_CANCELADA)
            self.assertEqual(reservas[1].estado, ESTADO_ACTIVA)
            self.assertEqual(reservas[0].solicitante, "Ana")
            self.assertEqual(reservas[1].solicitante, "Luis")
            self.assertEqual(reservas[0].unidad, "MIC-01")
            self.assertEqual(reservas[1].unidad, "MIC-02")
            for reserva, inicio, fin in (
                (reservas[0], primera.inicio, primera.fin),
                (reservas[1], segunda.inicio, segunda.fin),
            ):
                self.assertEqual(reserva.inicio, inicio)
                self.assertEqual(reserva.fin, fin)
                self.assertEqual(
                    reserva.inicio.utcoffset().total_seconds(), -10800
                )
                self.assertEqual(
                    reserva.fin.utcoffset().total_seconds(), -10800
                )

            tercera = reiniciado.crear(
                "MIC-01",
                "Mara",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )

            self.assertEqual(tercera.id, "RES-003")

    def test_consulta_tras_reiniciar_respeta_estados(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "reservas.json"
            repositorio = self.crear_repositorio(ruta)
            cancelada = repositorio.crear(
                "MIC-01",
                "Ana",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )
            repositorio.crear(
                "MIC-02",
                "Luis",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            )
            repositorio.cancelar(cancelada.id)
            reiniciado = self.crear_repositorio(ruta)

            self.assertTrue(
                reiniciado.consultar_disponibilidad(
                    "MIC-01",
                    "2026-10-29T10:00:00-03:00",
                    "2026-10-29T11:00:00-03:00",
                )
            )
            self.assertFalse(
                reiniciado.consultar_disponibilidad(
                    "MIC-02",
                    "2026-10-29T10:00:00-03:00",
                    "2026-10-29T11:00:00-03:00",
                )
            )

    def test_archivo_corrupto_da_error_y_no_se_modifica(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "reservas.json"
            contenido = "{ JSON inválido"
            ruta.write_text(contenido, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "JSON inválido"):
                self.crear_repositorio(ruta)

            self.assertEqual(ruta.read_text(encoding="utf-8"), contenido)


if __name__ == "__main__":
    unittest.main()
