from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("categories/", views.categories_pull, name="categories_pull"),
    path("products/", views.products_pull, name="products_pull"),
    path("barcodes/", views.barcodes_pull, name="barcodes_pull"),
    path("deletes/", views.deletes_pull, name="deletes_pull"),
    path("sync/push/", views.sync_push, name="sync_push"),
]
