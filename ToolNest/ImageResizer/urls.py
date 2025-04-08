

from django.urls import path
from ImageResizer import views

urlpatterns = [
    
    path('',views.resizeimage, name = 'resizeimage')
    
] 