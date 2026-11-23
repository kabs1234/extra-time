from django.urls import path

from accounts import views

urlpatterns = [
    path("auth/signup/", views.SignupView.as_view(), name="signup"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/refresh/", views.RefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("me/", views.MeView.as_view(), name="me"),
    path("me/password/", views.PasswordChangeView.as_view(), name="me-password"),
]
