from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('fornitori/', views.FornitoreListView.as_view(), name='Fornitori-list'),
]