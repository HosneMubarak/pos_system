from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

handler404 = 'account.views.custom_404_view'

urlpatterns = [
                  path('super-a-d-m-i-n/', admin.site.urls),
                  path('auth/', include('account.urls')),
                  path('', include('pos.urls')),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
