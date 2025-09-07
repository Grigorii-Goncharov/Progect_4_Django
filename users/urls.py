from django.urls import path
from .views import (
    UserRegisterView,
    UserLoginView,
    UserProfileEditView,
    UserProfileView,
    email_verification,
)
from django.contrib.auth.views import LogoutView

app_name = "users"


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("profile", UserProfileView.as_view(), name="profile"),
    path("profile_edit/", UserProfileEditView.as_view(), name="profile_edit"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("email-confirm/<str:token>/", email_verification, name="email-confirm"),
]
