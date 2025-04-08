
from django.urls import path
from ConvertlyX import views

urlpatterns = [

    path('', views.index, name = 'index'),
    path('<str:conversion_type>/', views.converter, name='converter'),
    path('upload/<str:conversion_type>/', views.upload, name='upload'),
    
] 



