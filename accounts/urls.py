from django.urls import path
from . import views
from . import api_views
urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register, name='register'),

   path('create_or_add_points/', api_views.create_or_add_points, name='create_or_add_points'),


]







