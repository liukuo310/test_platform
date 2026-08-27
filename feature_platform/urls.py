from django.urls import path
from feature_platform import views

urlpatterns = [
    path('feature_platform_main/', views.feature_platform_view, name='feature_platform_view'),
    path('api/update_user_level/', views.update_user_level, name='update_user_level'),
    path('api/update_user_points/', views.update_user_points, name='update_user_points'),
    path('api/update_user_status/', views.update_user_status, name='update_user_status'),
    path('api/batch_operation/', views.batch_operation, name='batch_operation'),
]