from django.contrib import admin
from core import views as core_views
from django.urls import path, include
from django.conf.urls import handler400, handler403, handler404, handler500

handler400 = core_views.custom_error
handler403 = core_views.custom_error
handler404 = core_views.custom_error
handler500 = core_views.custom_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # core uygulamasının URL'lerini ana projeye dahil ediyoruz
]
