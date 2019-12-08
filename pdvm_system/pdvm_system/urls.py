"""pdvm_system URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('authentication.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', TemplateView.as_view(template_name="index.html")),
   # path('', TemplateView.as_view(template_name='home.html'), name='home'), 
]
 