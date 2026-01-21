from django.urls import path
from api_platform import views

urlpatterns = [
    path('api_main_view/', views.api_main_view, name="api_main_view"),
    path('case_manage_view/', views.case_manage_view, name='case_manage_view'),
    path('api_manage_view/', views.api_manage_view, name='api_manage_view'),
    path('ci_di/', views.ci_di, name='ci_di'),
    # 接口操作
    path("create_api/", views.post_api, name="post_api"),
    path("updateApiPath/", views.put_api, name="put_api"),
    path("query_api/", views.get_api, name="get_api"),
    path("delete_api/", views.delete_api, name="delete_api"),

]
