from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import customer_logout

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("redirect/", views.merchant_redirect, name="redirect"),

    path("customer/register/<slug:store_slug>/", views.customer_register, name="customer_register"),
    path("customer/logout/", customer_logout, name="customer_logout"),

    path("<slug:store_slug>/customer/login/", views.customer_login, name="customer_login"),
    path("<slug:store_slug>/customer/quick-register/", views.quick_register, name="quick_register"),
]

