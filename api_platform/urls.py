from django.urls import path
from api_platform import views

urlpatterns = [
    path('', views.test_platform, name="performance_main_view"),
]
