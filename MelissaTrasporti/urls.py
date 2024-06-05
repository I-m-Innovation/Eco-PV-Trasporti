from django.contrib import admin
from django.urls import path, include, re_path
from . import views


urlpatterns = [
    path('fornitori/', views.FornitoreListView.as_view(), name='Fornitori-list'),
    path('commesse/', views.CommessaListView.as_view(), name='Commesse-list'),
    path('', views.home, name='home'),
    re_path(
        r'^comune-autocomplete/$',
        views.ComuneAutocomplete.as_view(),
        name='comune-autocomplete',
    ),
]