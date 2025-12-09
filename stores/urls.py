

from django.urls import path
from . import views
app_name = "stores"
urlpatterns = [
    path("", views.store_list, name="store_list"),

    # صفحة العرض العامة للمتجر (index1)
    path("<slug:slug>/", views.store_front, name="store_front"),

    path("store/<slug:store_slug>/product/public/<int:product_id>/", views.product_public, name="product_public"),
# ================== طرق الدفع ==================
    path(
        "dashboard/<slug:store_slug>/settings/payment-methods/",
        views.payment_methods_list,
        name="payment_methods"
    ),

    path(
        "dashboard/<slug:store_slug>/settings/payment-methods/add/",
        views.payment_methods_add,
        name="payment_methods_add"
    ),

    path(
        "dashboard/<slug:store_slug>/settings/payment-methods/<int:method_id>/edit/",
        views.payment_methods_edit,
        name="payment_methods_edit"
    ),

    path(
        "dashboard/<slug:store_slug>/settings/payment-methods/<int:method_id>/delete/",
        views.payment_methods_delete,
        name="payment_methods_delete"
    ),    ]

