import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .geo import _comuni_index, normalizza_localita, trova_comune
from .models import Comune, OffertaCommessa
from .views import _importa_offerte_commesse


class GeoResolverTests(TestCase):
    def setUp(self):
        _comuni_index.cache_clear()
        Comune.objects.bulk_create([
            Comune(cap="57025", name="Piombino", provincia="LI", latitudine=42.9219385, longitudine=10.5274135),
            Comune(cap="41026", name="Pavullo nel Frignano", provincia="MO", latitudine=44.3394593, longitudine=10.8339861),
            Comune(cap="24060", name="San Paolo d'Argon", provincia="BG", latitudine=45.6876437, longitudine=9.8017486),
            Comune(cap="40050", name="Castello d'Argile", provincia="BO", latitudine=44.6812258, longitudine=11.2965999),
            Comune(cap="5035", name="Narni", provincia="TR", latitudine=42.5192207, longitudine=12.5152876),
        ])

    def test_normalizza_apostrofi_accenti_e_spazi(self):
        self.assertEqual(normalizza_localita("Albaredo d' Adige"), "albaredo d adige")
        self.assertEqual(normalizza_localita("Nardo'"), "nardo")
        self.assertEqual(normalizza_localita("Scorze"), "scorze")

    def test_risolve_localita_e_refusi_noti(self):
        self.assertEqual(trova_comune("Populonia Stazione").name, "Piombino")
        self.assertEqual(trova_comune("Pavulla nel Frignano").name, "Pavullo nel Frignano")
        self.assertEqual(trova_comune("San Poalo D'Argon").name, "San Paolo d'Argon")
        self.assertEqual(trova_comune("Castelllo D'Argile").name, "Castello d'Argile")
        self.assertEqual(trova_comune("Capitone").name, "Narni")
        self.assertEqual(trova_comune("Capitone", provincia="TR").name, "Narni")


class ExcelImportTests(TestCase):
    def setUp(self):
        _comuni_index.cache_clear()
        Comune.objects.bulk_create([
            Comune(cap="57025", name="Piombino", provincia="LI", latitudine=42.9219385, longitudine=10.5274135),
            Comune(cap="25121", name="Brescia", provincia="BS", latitudine=45.5415526, longitudine=10.2118019),
        ])

    def _uploaded_workbook(self, filename, rows, sheet_title="2026"):
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = sheet_title
        for row in rows:
            sheet.append(row)

        buffer = io.BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        return SimpleUploadedFile(
            filename,
            buffer.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    def test_importa_offerte_da_header_non_in_prima_riga(self):
        file_obj = self._uploaded_workbook(
            "01_Riepilogo_OFFERTE_Eco-Pv_2026.xlsx",
            [
                ["OFFERTE ECO-PV 2026"],
                ["N.", "PRODUTTORE", "NOME RIF.", "MAIL RIF.", None, "COD. OFFERTA", "DATA OFFERTA", "COD. OCB", "COD. COMMESSA", "DATA CONTRATTO", "CONTRATTO ACCETTATO", "CATEGORIA", "GARANZIA FINANZIARIA", "Q.TA'", "TIPO", "PESO STIMATO (KG)", "VIAGGI STIMATI", "LUOGO RITIRO", "PROV"],
                [1, "CALZIFICIO ILARY SRL", "Paola", "mail@example.com", "M-E-M", "OSB_26001", None, "CO_26001", "CR_26038", None, None, "MOD", "ANTE", 33, "Poli", 660, 1, "Brescia", "BS"],
            ],
        )

        creati, aggiornati, saltati = _importa_offerte_commesse(file_obj)

        self.assertEqual((creati, aggiornati, saltati), (1, 0, 0))
        record = OffertaCommessa.objects.get(codice="OSB_26001")
        self.assertFalse(record.is_commessa)
        self.assertEqual(record.produttore, "CALZIFICIO ILARY SRL")
        self.assertEqual(record.quantita, 33)
        self.assertEqual(record.garanzia_fin, "ANTE")
        self.assertEqual(record.paese.name, "Brescia")

    def test_importa_commesse_da_header_operativo(self):
        file_obj = self._uploaded_workbook(
            "02_Riepilogo_COMMESSE_Eco-PV_2026.xlsx",
            [
                ["ECO-PV | GESTIONE GENERALE COMMESSE RTT 2026 - CONTROLLO OPERATIVO", "COD. COMMESSA", "PRODUTTORE", None, None, None, None, None, None, "GARANZIA FINANZIARIA", "Q.TA", "TIPO", None, None, "LUOGO RITIRO", "PROVINCIA"],
                [None, "x", "x", None, None, None, None, None, None, "x", "x", "x", None, None, "x", "x"],
                ["N.", "COD. COMMESSA", "PRODUTTORE", "NOME RIF.", "MAIL RIF.", "RIF. ECO-PV", "COD. OSB", "RIF. CC-CO", "CATEGORIA", "GARANZIA FINANZIARIA", "Q.TA'", "TIPO", "PESO STIMATO (KG)", "VIAGGI STIMATI", "LUOGO RITIRO", "PROV", "TRASPORTATORE", "CENTRO TRATTAMENTO", "DATA RITIRO", "II COPIA FIR", "REDAZIONE DOC GSE", "DICH AVV CONS", "INVIO DOC GSE CENTRO TRATT", "CERT AVV TRATT", "INVIO CLIENTE", "NR FATTURA", "DATA FATTURA", "IMPONIBILE", "PAGAMENTO", "PROCESSO COMPLETATO"],
                [1, "CR_26001", "SOCIETA AGRICOLA", "Andrea", "mail@example.com", "M-E-M", "OSB_25411", "CC_26001", "MOD", "-", 89, "Film Sottile", 1481.3, 1, "Piombino", "LI", "ECS-ERP", "ECS-ERP", None, "SI", "SI", "SI", "-", "-", "-", 78, None, 1500, None, "SI"],
            ],
            sheet_title="2026_GESTIONE",
        )

        creati, aggiornati, saltati = _importa_offerte_commesse(file_obj)

        self.assertEqual((creati, aggiornati, saltati), (1, 0, 0))
        record = OffertaCommessa.objects.get(codice="CR_26001")
        self.assertTrue(record.is_commessa)
        self.assertTrue(record.is_done)
        self.assertEqual(record.quantita, 89)
        self.assertEqual(record.tipologia, "Film Sottile")
        self.assertEqual(record.paese.name, "Piombino")
