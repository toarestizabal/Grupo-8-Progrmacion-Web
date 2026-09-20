from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy

urlpatterns = [
    path("django-admin/", admin.site.urls),
    # Alias global requerido por el correo estándar de recuperación de Django.
    path(
        "cuenta/recuperar/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("tienda:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path("", include("tienda.urls")),
]

handler403 = "tienda.views.error_403"
handler404 = "tienda.views.error_404"
