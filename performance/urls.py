from django.urls import path

from performance.views.client_views import performance_main_view, get_device_info, select_test_template, \
    get_android_performance_info, get_phone_message, result_report, get_ios_sq_info, ios_collect
from performance.views.service_views import service_performance_main, service_performance, \
    init_performance_conf, get_performance_data, stop_performance_collect, monitor_stress_server

urlpatterns = [
    path('performance_main', service_performance_main, name="service_performance_main"),
    # 客户端性能接口
    path('client_performance_main', performance_main_view, name="performance_main_view"),
    path('get_device_info', get_device_info, name="get_device_info"),
    path('select_test_template', select_test_template, name="select_test_template"),
    path('get_android_info', get_android_performance_info, name='android_info'),
    path("get_phone_message", get_phone_message, name="get_phone_message"),
    path("result_report", result_report, name="result_report"),
    path('get_one_ios_info', get_ios_sq_info, name="get_one_ios_info"),
    path('init_ios_script', ios_collect, name='init_ios_script'),

    # 服务端性能接口
    path('service/main', service_performance_main, name="service_performance_main"),
    path('service/page', service_performance, name="service_performance"),
    path('service/init', init_performance_conf, name="init_performance_conf"),
    path('service/collect', get_performance_data, name="get_performance_data"),
    path('service/stop', stop_performance_collect, name="stop_performance_collect"),
    # 施压服务器监控接口（新增）
    path('stress/monitor', monitor_stress_server, name="monitor_stress_server"),
]
