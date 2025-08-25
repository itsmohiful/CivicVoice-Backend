from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views import defaults as default_views
from django.urls import include, path, re_path
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from graphene_django.views import GraphQLView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from graphene_file_upload.django import FileUploadGraphQLView
from civicvoice_backend.users.api.views import RegisterView, MeView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)


urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("civicvoice_backend.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Complaints system
    path("complaints/", include("civicvoice_backend.complaints.urls", namespace="complaints")),
    # Complaints system
    # Dashboard
    #path("dashboard/", include("civicvoice_backend.dashboard.urls", namespace="dashboard")),
    # Settings
    #path("settings/", include("civicvoice_backend.setting.urls", namespace="settings")),
    # REST API
    path("api/", include("civicvoice_backend.complaints.api.urls")),
    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    # path('api/registration/', RegistrationView.as_view(), name='registration'),
    # path("api/register/", RegisterView.as_view(), name="register"),
    # path("api/me/", MeView.as_view(), name="me"),
    # path('api/auth/', include('dj_rest_auth.urls')),           # login/logout
    # path('api/auth/registration/', include('dj_rest_auth.registration.urls'))

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()
urlpatterns += [
    path('graphql/', csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True))),
]

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
