"""
Driver Portal URLs
Dedicated URLs for driver delivery management
"""

from django.urls import path
from ..views_driver_portal import (
    driver_login,
    driver_logout,
    driver_dashboard,
    driver_deliveries,
    driver_delivery_detail,
    driver_update_status,
    driver_profile,
    driver_update_location,
)

app_name = 'driver_portal'

urlpatterns = [
    # Authentication
    path('login/', driver_login, name='login'),
    path('logout/', driver_logout, name='logout'),
    
    # Dashboard
    path('', driver_dashboard, name='dashboard'),
    
    # Deliveries
    path('deliveries/', driver_deliveries, name='deliveries'),
    path('deliveries/<int:order_id>/', driver_delivery_detail, name='delivery_detail'),
    path('deliveries/<int:order_id>/update-status/', driver_update_status, name='update_status'),
    
    # Profile
    path('profile/', driver_profile, name='profile'),
    
    # Status updates
    path('update-location/', driver_update_location, name='update_location'),
]
