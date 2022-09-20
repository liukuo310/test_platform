from django.urls import path

from plat.views import login_view, register_view, Register

urlpatterns = [
    path('', login_view, name="登录首页"),
    path('register_view', register_view, name="注册试图函数"),
    path('register', Register.as_view(), name="用户注册")
]
