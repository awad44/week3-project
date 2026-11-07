"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT Authentication
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/token/verify/",
        TokenVerifyView.as_view(),
        name="token_verify",
    ),
    path(
        "api/token/blacklist/",
        TokenBlacklistView.as_view(),
        name="token_blacklist",
    ),
    # OpenAPI schema and Swagger UI must precede the version catch-all routes.
    path(
        "api/schema/v1/",
        SpectacularAPIView.as_view(api_version="v1"),
        name="schema-v1",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema-v1"),
        name="swagger-ui",
    ),
    path(
        "api/schema/v2/",
        SpectacularAPIView.as_view(api_version="v2"),
        name="schema-v2",
    ),
    path(
        "api/docs/v2/",
        SpectacularSwaggerView.as_view(url_name="schema-v2"),
        name="swagger-v2",
    ),
    # Keep session login for our browsable API.
    path(
        "api-auth/",
        include(
            "rest_framework.urls",
            namespace="rest_framework",
        ),
    ),
    # Original API
    path("api/", include("tasks.urls")),
    path("api/", include("projectapp.urls")),
    # Versioned API
    path("api/<str:version>/", include("tasks.urls")),
    path("api/<str:version>/", include("projectapp.urls")),
]
