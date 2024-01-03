# urls.py

#from django.contrib import admin
from django.urls import path
from prediksiwema import views
from prediksiwema.views import calculate_wema
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='input'),
    path('hasil_wema/', views.calculate_wema, name='calculate_wema'),
    path('grafik/', views.grafik, name='grafik'),
    # path('grafik/', views.grafik_mape, name='grafik'),
]

# Tambahkan konfigurasi URL untuk media files
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)