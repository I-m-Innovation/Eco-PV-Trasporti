from django.contrib import admin
from django.urls import path, include, re_path
from . import views

admin.site.site_title = "Gestione commesse"
admin.site.site_header = "Eva & Melissa Trasporti Inc."
admin.site.index_title = "Portale gestione commesse"

urlpatterns = [
    path('', views.home, name='home'),
    re_path(
        r'^comune-autocomplete/$',
        views.ComuneAutocomplete.as_view(),
        name='comune-autocomplete',
    ),
]

