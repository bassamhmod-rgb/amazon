from django.urls import path
from . import views_api

urlpatterns = [
    path("api/categories/<int:merchant_id>/", views_api.merchant_categories_api),
    path("api/products/<int:merchant_id>/", views_api.merchant_products_api),
    path(
        "api/create_product_from_access/",
        views_api.create_product_from_access,
        name="create_product_from_access"
        ),
]
