from django.urls import path
from api_platform import views

urlpatterns = [
    path('api_main_view/', views.api_main_view, name="api_main_view"),
    path('case_manage_view/', views.case_manage_view, name='case_manage_view'),
    path('api_manage_view/', views.api_manage_view, name='api_manage_view'),
    path('ci_di/', views.ci_di, name='ci_di'),
    # 原生接口操作
    path("create_api/", views.create_api, name="create_api"),
    path("update_api/", views.update_api, name="update_api"),
    path("query_api/", views.get_api, name="get_api"),
    path("delete_api/", views.delete_api, name="delete_api"),
    # 使用接口操作
    path("create_using_api/", views.create_using_api, name="create_using_api"),
    path("update_using_api/", views.update_using_api, name="update_using_api"),
    path("query_using_api/", views.query_using_api, name="query_using_api"),
    path("delete_using_api/", views.delete_using_api, name="delete_using_api"),
    # 用例操作
    path("create_case/", views.create_case, name="create_case"),
    path("update_case/", views.update_case, name="update_case"),
    path("query_case/", views.get_case, name="get_case"),
    path("delete_case/", views.delete_case, name="delete_case"),

    path("test/", views.test_case, name="test_case")  # 平台测试接口使用
]
