from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('cortex/api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('cortex/api/schema/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('cortex/api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('cortex/admin/', admin.site.urls),
    path('cortex/auth/', include('Auth.urls')),
    path('cortex/identidade/', include('Identidade.urls')),
    path('cortex/organizacional/', include('Organizacional.urls')),
    path('cortex/pessoas-institucionais/', include('PessoasInstitucionais.urls')),
    path('cortex/academico/', include('Academico.urls')),
    path('cortex/infraestrutura/', include('Infraestrutura.urls')),
    path('cortex/transporte/', include('Transporte.urls')),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
