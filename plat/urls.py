from django.urls import path
from plat.views import login_view, register_view, Register, login, main_view

urlpatterns = [
    path('', login_view, name="登录首页"),
    path('login', login, name="登录"),
    path('register_view', register_view, name="注册试图函数"),
    path('register', Register.as_view(), name="用户注册"),
    path('main_view/', main_view, name="平台登录后选择主页面"),
]
