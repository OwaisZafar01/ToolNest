

from django.urls import path,include
from URL_Shortener import views

urlpatterns = [
   
    path("",views.urlshorten, name = 'urlshorten')

] 

