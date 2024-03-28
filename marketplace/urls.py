from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
   openapi.Info(
      title="Digitvl Streaming API",
      default_version='v1',
      description="API For Digitvl Streaming",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@digitvl.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
                  path("", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
                  path(
                      "api/v1/redoc/",
                      schema_view.with_ui("redoc", cache_timeout=0),
                      name="schema-redoc",
                  ),
                  path('admin/', admin.site.urls),
                  path('api/v1/', include('accounts.urls')),
                  path('api/v1/', include('announcement.urls')),
                  path('api/v1/', include('advertisement.urls')),
                  path('api/v1/', include('userdata.urls')),
                  path('api/v1/', include('beats.urls')),
                  path('api/v1/', include('feeds.urls')),
                  path('api/v1/', include('donations.urls')),
                  path('api/v1/', include('redeemCoins.urls')),
                  path('api/v1/', include('support.urls')),
                  path('api/v1/', include('tweets.urls')),
                  path('api/v1/', include('blogs.urls')),
                  path('api/v1/', include('invitation.urls')),
                  path('api/v1/', include('subscriptions.urls')),
                  path('api/v1/', include('linktree.urls')),
                  path('api/v1/', include('xrpwallet.urls')),
                  path("stripe/", include("djstripe.urls", namespace="djstripe")),


              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)




