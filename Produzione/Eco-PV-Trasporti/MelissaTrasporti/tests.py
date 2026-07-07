from django.test import TestCase

from .geo import _comuni_index, normalizza_localita, trova_comune
from .models import Comune


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
