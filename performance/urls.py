from django.urls import path
from performance.views import performance_main_view

urlpatterns = [
    path('performance_main/', performance_main_view, name="登录首页"),
]
