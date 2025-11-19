from django.urls import include, path
from . import views
app_name='laptop'
urlpatterns = [
    path('', views.product,name='home'),
    path('about', views.about, name='about'),
    path('laptop_shop', views.laptop_shop , name='laptop_shop'),
    path('laptop_accessory', views.accessoryl , name='acessoryl'),
    path('mobile_accessory', views.accessorym , name='acessorym'),
    path('contact us', views.contact , name='contact'),

    path('laptop_details/<int:id>/', views.laptop_details , name='laptop_details'),
    path('laptop_accessory_detail/<int:id>/', views.accessl_details , name='laptop_accessory_details'),
    path('mobile_accessory_detail/<int:id>/', views.accessm_details , name='mobile_accessory_details'),

    path('service_det_all/<int:id>/', views.service_det_all, name='service_det_all'),
    path('laptops/<str:brand_name>/', views.laptop_by_brand, name='laptop_by_brand'),
    path('products/<str:category_name>/', views.products_by_category, name='products_by_category'),
   
   


]
