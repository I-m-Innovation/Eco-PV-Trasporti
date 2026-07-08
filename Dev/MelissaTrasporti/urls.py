from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views
from . import views

admin.site.site_title = "Gestione commesse"
admin.site.site_header = "Eva & Melissa Trasporti Inc."
admin.site.index_title = "Portale gestione commesse"

urlpatterns = [
    path('login/', views.AppLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('carica-excel/', views.carica_excel, name='carica_excel'),
    path('', views.home, name='home'),
    re_path(
        r'^comune-autocomplete/$',
        views.ComuneAutocomplete.as_view(),
        name='comune-autocomplete',
    ),
]

