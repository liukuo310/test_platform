from django.urls import path
from performance import views

urlpatterns = [
    path('performance_main/', views.performance_main_view, name="performance_main_view"),
    path('get_device_info', views.get_device_info, name="get_device_info"),
    path('select_test_template', views.select_test_template, name="select_test_template"),
    path('get_android_info', views.get_android_performance_info, name='android_info'),  # 获得一帧安卓设备数据
    path("get_phone_message", views.get_phone_message, name="get_phone_message"),  # 获得手机设备信息
    path("result_report", views.result_report, name="result_report")
]
