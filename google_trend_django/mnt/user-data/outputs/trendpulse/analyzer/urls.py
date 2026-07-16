from django.urls import path
from . import views

urlpatterns = [
    path('',                views.index,       name='index'),
    path('api/status/',     views.api_status,  name='api_status'),
    path('api/trends/',     views.api_trends,  name='api_trends'),
    path('api/regions/',    views.api_regions, name='api_regions'),
    path('api/related/',    views.api_related, name='api_related'),
    path('api/compare/',    views.api_compare, name='api_compare'),
]
