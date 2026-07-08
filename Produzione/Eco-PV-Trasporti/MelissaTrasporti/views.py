from django.views.generic.list import ListView
from django.shortcuts import render, redirect, resolve_url
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.contrib import messages
from urllib.parse import urlparse
import math
import re
import csv
import io

from dal import autocomplete

from MelissaTrasporti.geo import trova_comune
from MelissaTrasporti.forms import ExcelUploadForm
from MelissaTrasporti.models import Fornitore, Commessa, Comune, OffertaCommessa

import folium
import numpy as np
import geopy as geo

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="melissa_trasporti_inc")


def _normalizza_colonna(nome):
    return re.sub(r'[^a-z0-9]+', '_', str(nome).strip().lower()).strip('_')


def _valore(record, *nomi):
    for nome in nomi:
        valore = record.get(nome)
        if valore is not None and not (isinstance(valore, float) and math.isnan(valore)):
            testo = str(valore).strip()
            if testo and testo.lower() != 'nan':
                return valore
    return None


def _bool_import(record, nome, default=False):
    valore = _valore(record, nome)
    if valore is None:
        return default
    if isinstance(valore, bool):
        return valore
    return str(valore).strip().lower() in {'1', 'true', 'vero', 'si', 's', 'yes', 'y', 'x'}


def _float_import(record, *nomi):
    valore = _valore(record, *nomi)
    if valore is None:
        return None
    try:
        return float(str(valore).replace(',', '.'))
    except ValueError:
        return None


def _records_da_file(file_obj):
    nome_file = file_obj.name.lower()
    if nome_file.endswith('.csv'):
        text_file = io.TextIOWrapper(file_obj.file, encoding='utf-8-sig')
        return list(csv.DictReader(text_file))

    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise ValueError('per importare file Excel serve installare openpyxl. In alternativa carica un CSV.') from exc

    workbook = load_workbook(file_obj, read_only=True, data_only=True)
    records = []
    for sheet in workbook.worksheets:
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows, None)
        if not headers:
            continue
        headers = [_normalizza_colonna(header) for header in headers]
        for row in rows:
            records.append(dict(zip(headers, row)))
    return records


def _importa_offerte_commesse(file_obj):
    records = _records_da_file(file_obj)

    creati = 0
    aggiornati = 0
    saltati = 0

    for row in records:
        row = {_normalizza_colonna(key): value for key, value in row.items()}
        codice = _valore(row, 'codice', 'codice_offerta', 'codice_commessa')
        produttore = _valore(row, 'produttore', 'cliente', 'ragione_sociale')
        tipologia = _valore(row, 'tipologia', 'tipo')
        quantita = _valore(row, 'quantita', 'qta', 'q_ta')
        if not codice or not produttore or not tipologia or quantita is None:
            saltati += 1
            continue

        localita = _valore(row, 'localita', 'comune', 'paese', 'luogo_ritiro')
        provincia = _valore(row, 'provincia', 'prov')
        comune = trova_comune(localita, provincia) if localita else None

        dati = {
            'produttore': str(produttore).strip(),
            'garanzia_fin': str(_valore(row, 'garanzia_fin', 'garanzia', 'garanzia_finanziaria') or '-').strip(),
            'quantita': int(float(str(quantita).replace(',', '.'))),
            'tipologia': str(tipologia).strip(),
            'note': str(_valore(row, 'note') or '').strip(),
            'latitudine': _float_import(row, 'latitudine', 'lat'),
            'longitudine': _float_import(row, 'longitudine', 'lon', 'lng'),
            'is_commessa': _bool_import(row, 'is_commessa', False),
            'is_done': _bool_import(row, 'is_done', False),
        }
        if comune:
            dati['paese'] = comune

        _, creato = OffertaCommessa.objects.update_or_create(
            codice=str(codice).strip(),
            defaults=dati,
        )
        creati += int(creato)
        aggiornati += int(not creato)

    return creati, aggiornati, saltati


class AppLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def _is_login_redirect(self, redirect_to):
        return urlparse(redirect_to).path == self.request.path

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        redirect_to = context.get(self.redirect_field_name)
        context['safe_next'] = redirect_to if redirect_to and not self._is_login_redirect(redirect_to) else ''
        return context

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to and not self._is_login_redirect(redirect_to):
            return redirect_to
        return resolve_url(settings.LOGIN_REDIRECT_URL)


def applica_geolocalizzazione(record, localita=None, provincia=None):
    if record.get('latitudine') and record.get('longitudine'):
        return record

    localita = localita or record.get('localita') or record.get('luogo_ritiro') or record.get('paese__name')
    provincia = provincia or record.get('provincia') or record.get('paese__provincia')
    comune = trova_comune(localita, provincia)
    if not comune:
        return record

    record['latitudine'] = comune.latitudine
    record['longitudine'] = comune.longitudine
    record['paese__latitudine'] = comune.latitudine
    record['paese__longitudine'] = comune.longitudine
    record['paese__name'] = comune.name
    record['paese__provincia'] = comune.provincia
    return record


def anno_da_codice(codice):
    match = re.search(r'(?:^|[_\-\s])(\d{2})\d{3}', str(codice or ''))
    if not match:
        return ''
    anno = 2000 + int(match.group(1))
    return anno if 2000 <= anno <= 2099 else ''


def prepara_record_tabella(record):
    record = applica_geolocalizzazione(record)
    is_commessa = bool(record.get('is_commessa'))
    is_done = bool(record.get('is_done'))
    record['tipo_record'] = 'Commessa' if is_commessa else 'Offerta'
    record['stato_record'] = 'Evasa' if is_done else ('In carico' if is_commessa else 'Offerta')
    record['anno_record'] = anno_da_codice(record.get('codice'))
    return record


class ComuneAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Comune.objects.none()

        qs = Comune.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q) | qs.filter(cap__istartswith=self.q) | qs.filter(provincia__istartswith=self.q)
        return qs


@login_required
def home(request):
    fornitori = list(Fornitore.objects.values(
        'id',
        'ragione_sociale',
        'indirizzo',
        'trasporto',
        'trattamento',
        'latitudine',
        'longitudine',
        'paese__cap',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))
    commesse = list(Commessa.objects.filter(is_done=False).values(
        'id',
        'codice',
        'produttore',
        'garanzia_fin',
        'quantita',
        'note',
        'tipologia',
        'latitudine',
        'longitudine',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))
    offerte = list(OffertaCommessa.objects.filter(is_commessa=False).values(
        'id',
        'codice',
        'produttore',
        'garanzia_fin',
        'quantita',
        'note',
        'tipologia',
        'latitudine',
        'longitudine',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))
    dati_tabella = list(OffertaCommessa.objects.all().values(
        'id',
        'codice',
        'produttore',
        'garanzia_fin',
        'quantita',
        'note',
        'tipologia',
        'latitudine',
        'longitudine',
        'is_commessa',
        'is_done',
        'paese__cap',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))
    fornitori = [applica_geolocalizzazione(fornitore) for fornitore in fornitori]
    commesse = [applica_geolocalizzazione(commessa) for commessa in commesse]
    offerte = [applica_geolocalizzazione(offerta) for offerta in offerte]
    dati_tabella = [prepara_record_tabella(record) for record in dati_tabella]

    context = {
        'fornitori_list': fornitori,
        'commesse_list': commesse,
        'offerte_list': offerte,
        'dati_tabella_list': dati_tabella,
        'upload_form': ExcelUploadForm(),
        'open_upload_panel': request.GET.get('upload') == '1',
    }
    return render(request, 'HomePage.html', context)


@login_required
def carica_excel(request):
    if request.method == 'POST':
        form = ExcelUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                creati, aggiornati, saltati = _importa_offerte_commesse(form.cleaned_data['file'])
                messages.success(
                    request,
                    f'Import completato: {creati} creati, {aggiornati} aggiornati, {saltati} righe saltate.'
                )
                return redirect(f'{resolve_url("home")}?upload=1')
            except Exception as exc:
                messages.error(request, f'Import non riuscito: {exc}')
                return redirect(f'{resolve_url("home")}?upload=1')

        messages.error(request, 'Seleziona un file Excel o CSV valido.')
        return redirect(f'{resolve_url("home")}?upload=1')

    return redirect(f'{resolve_url("home")}?upload=1')
