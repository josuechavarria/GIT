"""GIT URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from evaluaciones.views import LoginView
from evaluaciones import views as evaluaciones_views
from django.conf.urls import handler404, handler500

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/login/', LoginView.as_view(), name='login'),
    url(r'^evaluaciones/', include('evaluaciones.urls', namespace='evaluaciones')),
]

from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = evaluaciones_views.error_404
handler500 = evaluaciones_views.error_500