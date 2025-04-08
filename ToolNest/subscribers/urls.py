
from django.urls import path
from . import views

app_name = 'subscribers'

urlpatterns = [
    path('', views.subscribe_newsletter, name='subscribe_newsletter'),
]