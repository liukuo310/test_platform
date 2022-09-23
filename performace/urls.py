from django.urls import path
from performace.views import performance_main_view

urlpatterns = [
    path('', performance_main_view, name="性能测试平台主页"),
]
