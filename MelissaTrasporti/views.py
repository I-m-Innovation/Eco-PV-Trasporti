from django.views.generic.list import ListView
from django.shortcuts import render
from django.core import serializers

from dal import autocomplete

from MelissaTrasporti.models import Fornitore, Commessa, Comune, OffertaCommessa

import folium
import numpy as np
import geopy as geo

from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="melissa_trasporti_inc")


class ComuneAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated:
            return Comune.objects.none()

        qs = Comune.objects.all()
        if self.q:
            qs = qs.filter(name__icontains=self.q) | qs.filter(cap__istartswith=self.q) | qs.filter(provincia__istartswith=self.q)
        return qs


def home(request):
    fornitori = list(Fornitore.objects.values())
    commesse = list(Commessa.objects.filter(is_done=False).values(
        'codice',
        'produttore',
        'garanzia_fin',
        'quantita',
        'tipologia',
        'latitudine',
        'longitudine',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))
    offerte = list(OffertaCommessa.objects.filter(is_commessa=False).values(
        'codice',
        'produttore',
        'garanzia_fin',
        'quantita',
        'tipologia',
        'latitudine',
        'longitudine',
        'paese__latitudine',
        'paese__longitudine',
        'paese__name',
        'paese__provincia',
    ))

    context = {
        'fornitori_list': fornitori,
        'commesse_list': commesse,
        'offerte_list': offerte,
    }
    return render(request, 'HomePage.html', context)
