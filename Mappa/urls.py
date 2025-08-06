from django.urls import path
from . import views

urlpatterns = [
    path('request-token/', views.request_token_view, name='request_token'),
    path('register/', views.register, name='register'),
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('index/', views.index, name='index'),
    path('upload-excel/', views.upload_excel, name='upload_excel'),
    path('api/map-data/', views.map_data, name='map_data'),
    path('api/table-data/', views.table_data, name='table_data'),
]
