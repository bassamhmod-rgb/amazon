from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import customer_logout
from . import views_api
from .views import customer_points
from .views_api import accounting_notifications

app_name = "accounts"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("redirect/", views.merchant_redirect, name="redirect"),

    path("customer/register/<slug:store_slug>/", views.customer_register, name="customer_register"),
    path("customer/logout/", customer_logout, name="customer_logout"),


    path("<slug:store_slug>/customer/login/", views.customer_login, name="customer_login"),
    path("<slug:store_slug>/customer/quick-register/", views.quick_register, name="quick_register"),
#لل api
    path("api/customers/<int:merchant_id>/", views_api.merchant_customers_api),
    path("api/suppliers/<int:merchant_id>/", views_api.merchant_suppliers_api),
    path("api/customers/confirm/", views_api.merchant_customers_confirm_api),
    path("api/suppliers/confirm/", views_api.merchant_suppliers_confirm_api),
    path(
        "api/create_customer_from_access/",
        views_api.create_customer_from_access,
        name="create_customer_from_access"
    ),
    path(
        "api/create_supplier_from_access/",
        views_api.create_supplier_from_access,
        name="create_supplier_from_access"
    ),
    path(
        "api/merchant/<int:merchant_id>/points/export/",
        views_api.merchant_points_export_api,
        name="merchant_points_export"
    ),
    path(
        "api/merchant/points/confirm/",
        views_api.merchant_points_confirm_api,
        name="merchant_points_confirm"
    ),
    # 🔹 استيراد النقاط من الأكسس إلى المتجر
    path(
        "api/merchant/<int:merchant_id>/points/import/",
        views_api.create_cashback_from_access,
        name="create_cashback_from_access"
    ),

    path(
        "api/get-customer-id/",
        views_api.get_customer_id_for_access,
        name="get_customer_id_for_access"
    ),
    #مسار صفحة النقاط للزبون
    path(
        "<slug:store_slug>/points/", customer_points, name="customer_points"),
#مسار الدخول للنقاط
path("<slug:store_slug>/customer/login/", views.customer_points_login, name="customer_points_login"),

   #path("<slug:store_slug>/customer/login/", views.customer_login, name="customer_login"),
  # للاشعارات
  # from django.urls import path

path(
        "api/accounting/notifications/",
        accounting_notifications,
        name="accounting_notifications"
    ),
path(
    "api/merchant/<int:merchant_id>/status/",
    views_api.merchant_status,
    name="merchant_status"
),
# للتحديث
path("api/check-update/", views_api.check_update)
   
    ]
