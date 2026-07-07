import re
import unicodedata
from functools import lru_cache

from .models import Comune


LOCALITA_TO_COMUNE = {
    "populonia stazione": "Piombino",
    "marina di vasto vasto": "Vasto",
    "castelceriolo": "Alessandria",
    "dimario folgarida": "Dimaro Folgarida",
    "villalta di cesenatico": "Cesenatico",
    "caprazzino": "Sassocorvaro Auditore",
    "capitone": "Narni",
    "macome": "Macomer",
}


REFUSI_COMUNI = {
    "pavulla nel frignano": "Pavullo nel Frignano",
    "san poalo d argon": "San Paolo d'Argon",
    "castelllo d argile": "Castello d'Argile",
    "due ville": "Dueville",
}


def normalizza_localita(value):
    value = str(value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("’", "'").replace("`", "'").replace("´", "'")
    value = re.sub(r"\s*'\s*", "'", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


@lru_cache(maxsize=1)
def _comuni_index():
    index = {}
    for comune in Comune.objects.all():
        index.setdefault(normalizza_localita(comune.name), []).append(comune)
    return index


def trova_comune(localita, provincia=None):
    normalized = normalizza_localita(localita)
    if not normalized:
        return None

    lookup_name = (
        LOCALITA_TO_COMUNE.get(normalized)
        or REFUSI_COMUNI.get(normalized)
        or localita
    )
    matches = _comuni_index().get(normalizza_localita(lookup_name), [])
    if not matches:
        return None

    normalized_provincia = normalizza_localita(provincia)
    if normalized_provincia:
        for comune in matches:
            if normalizza_localita(comune.provincia) == normalized_provincia:
                return comune

    return matches[0]
