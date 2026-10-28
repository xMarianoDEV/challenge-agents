import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from reservas.cli import main


INVENTARIO = {
    "MIC-01": "Microscopio digital",
    "MIC-02": "Microscopio digital",
}
AHORA = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        base = Path(self.directorio.name)
        self.ruta_inventario = base / "data" / "inventario.json"
        self.ruta_reservas = base / "data" / "reservas.json"
        self.ruta_inventario.parent.mkdir()
        self.ruta_inventario.write_text(
            json.dumps(INVENTARIO),
            encoding="utf-8",
        )

    def ejecutar(self, argumentos):
        salida = io.StringIO()
        errores = io.StringIO()
        with contextlib.redirect_stdout(salida), contextlib.redirect_stderr(errores):
            codigo = main(
                argumentos,
                ruta_inventario=self.ruta_inventario,
                ruta_reservas=self.ruta_reservas,
                reloj=lambda: AHORA,
            )
        return codigo, salida.getvalue(), errores.getvalue()

    def test_reservar_listar_y_cancelar(self):
        codigo, salida, errores = self.ejecutar(
            [
                "reservar",
                "MIC-01",
                "Ana",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            ]
        )
        self.assertEqual(codigo, 0)
        self.assertEqual(salida, "Reserva creada: RES-001\n")
        self.assertEqual(errores, "")

        codigo, salida, errores = self.ejecutar(["listar"])
        self.assertEqual(codigo, 0)
        self.assertIn("id\tunidad\tsolicitante\tinicio\tfin\testado", salida)
        self.assertIn(
            "RES-001\tMIC-01\tAna\t2026-10-29T10:00:00-03:00\t"
            "2026-10-29T11:00:00-03:00\tactiva",
            salida,
        )
        self.assertEqual(errores, "")

        codigo, salida, errores = self.ejecutar(["cancelar", "RES-001"])
        self.assertEqual(codigo, 0)
        self.assertEqual(salida, "RES-001 cancelada\n")
        self.assertEqual(errores, "")

        codigo, salida, errores = self.ejecutar(["listar"])
        self.assertEqual(codigo, 0)
        self.assertIn("\tcancelada\n", salida)
        self.assertEqual(errores, "")

    def test_error_de_dominio_sin_traceback(self):
        codigo, salida, errores = self.ejecutar(
            [
                "reservar",
                "NO-EXISTE",
                "Ana",
                "2026-10-29T10:00:00-03:00",
                "2026-10-29T11:00:00-03:00",
            ]
        )

        self.assertNotEqual(codigo, 0)
        self.assertEqual(salida, "")
        self.assertIn("Error: Unidad desconocida: NO-EXISTE", errores)
        self.assertNotIn("Traceback", errores)


if __name__ == "__main__":
    unittest.main()
