from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.ping, name="ping"),
    path("products/", views.products_pull, name="products_pull"),
    path("sync/push/", views.sync_push, name="sync_push"),
]

