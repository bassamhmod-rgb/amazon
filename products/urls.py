from django.urls import path
from . import views_api

urlpatterns = [
    path("api/categories/<int:merchant_id>/", views_api.merchant_categories_api),
    path("api/products/<int:merchant_id>/", views_api.merchant_products_api),

]
