
from django.urls import path
from DownloX import views

urlpatterns = [

    path('', views.download, name = 'download'),
     path('download-file/', views.download_file, name='download_file'),
   
] 





