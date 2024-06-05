from django.views.generic.list import ListView
from django.shortcuts import render

from dal import autocomplete

from MelissaTrasporti.models import Fornitore, Commessa, Comune
from MelissaTrasporti.forms import SelectTipoFornitori

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


class FornitoreListView(ListView):
    model = Fornitore
    template_name = 'FornitoriView.html'
    context_object_name = 'fornitori_list'
    success_url = "/"

class CommessaListView(ListView):
    model = Commessa
    template_name = 'CommesseView.html'
    context_object_name = 'commesse_list'
    success_url = "/"

def home(request):

    if request.POST.get('completo'):
        fornitori = Fornitore.objects.filter(trasporto=True).filter(trattamento=True)
        form = SelectTipoFornitori(initial={'completo': True, 'trasporto': False, 'trattamento': False})

    elif request.POST.get('trasporto') or request.POST.get('trattamento'):
        fornitori = Fornitore.objects.filter(trasporto=request.POST.get('trasporto') == 'on').filter(trattamento=False) | Fornitore.objects.filter(trattamento=request.POST.get('trattamento') == 'on').filter(trasporto=False)
        form = SelectTipoFornitori(initial={'completo': False, 'trasporto': request.POST.get('trasporto') == 'on', 'trattamento': request.POST.get('trattamento') == 'on'})

    else:
        fornitori = Fornitore.objects.all()
        form = SelectTipoFornitori(initial={'completo': False, 'trasporto': False, 'trattamento': False})

    m_lat = np.mean(list(fornitori.values_list('latitudine')))
    m_long = np.mean(list(fornitori.values_list('longitudine')))
    m = folium.Map(location=[m_lat, m_long], zoom_start=6, tiles='https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                   attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors')

    for fornitore in fornitori:
        coords = (fornitore.latitudine, fornitore.longitudine)
        if fornitore.trasporto and fornitore.trattamento:
            color, icon = 'orange', 'arrows-rotate'

        elif fornitore.trasporto:
            color, icon = 'darkblue', 'truck-fast'

        elif fornitore.trattamento:
            color, icon = 'darkgreen', 'recycle'

        folium.Marker(coords, popup=fornitore.ragione_sociale,
                      icon=folium.Icon(color=color, icon=icon, prefix='fa')).add_to(m)

    commesse = Commessa.objects.all()
    for commessa in commesse:
        coords = (commessa.paese.latitudine, commessa.paese.longitudine)
        colori = {'ANTE': 'purple', '-':'red'}
        color = colori[commessa.garanzia_fin]
        html="""
        <p style="margin: 5px 0">Commessa: {codice}</p>
        <p style="margin: 5px 0">Quantità: {quantita}</p>
        <p style="margin: 5px 0">Tipologia: {tipologia}</p>
        <p style="margin: 5px 0">Produttore: {produttore}</p>
        """.format(codice=commessa.codice, quantita=commessa.quantita, produttore=commessa.produttore, tipologia=commessa.tipologia)
        folium.Marker(coords, popup=html, icon=folium.Icon(color=color)).add_to(m)

    context = {'map': m._repr_html_(), 'fornitori_list': fornitori, 'form': form}
    return render(request, 'HomePage.html', context)
