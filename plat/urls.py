from django.urls import path

from plat.views import login_view, register_view, Register, login

urlpatterns = [
    path('', login_view, name="登录首页"),
    path('login', login, name="登录"),
    path('register_view', register_view, name="注册试图函数"),
    path('register', Register.as_view(), name="用户注册")
]
