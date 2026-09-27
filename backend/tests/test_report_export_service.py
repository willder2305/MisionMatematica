import unittest

from services.report_export_service import _texto_seguro, exportar_reporte


class ReportExportServiceTest(unittest.TestCase):
    def setUp(self):
        self.columnas = [("estudiante", "Estudiante"), ("intentos", "Intentos")]
        self.filas = [{"estudiante": "=dato externo", "intentos": 10}]

    def test_sanea_formulas_de_excel(self):
        self.assertEqual(_texto_seguro("=SUM(A1:A2)"), "'=SUM(A1:A2)")
        self.assertEqual(_texto_seguro("Estudiante"), "Estudiante")

    def test_genera_xlsx_valido(self):
        archivo, mimetype, nombre = exportar_reporte("xlsx", "Reporte QA", self.columnas, self.filas, "reporte_qa")
        self.assertEqual(mimetype, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertTrue(nombre.endswith(".xlsx"))
        self.assertTrue(archivo.read(2) == b"PK")

    def test_genera_pdf_valido(self):
        filas = [{"estudiante": "A < B & C", "intentos": 10}]
        archivo, mimetype, nombre = exportar_reporte("pdf", "Reporte < QA", self.columnas, filas, "reporte_qa")
        self.assertEqual(mimetype, "application/pdf")
        self.assertTrue(nombre.endswith(".pdf"))
        self.assertTrue(archivo.read(4) == b"%PDF")

    def test_no_exporta_reporte_vacio(self):
        self.assertIsNone(exportar_reporte("pdf", "Reporte QA", self.columnas, [], "reporte_qa"))


if __name__ == "__main__":
    unittest.main()
