from django.urls import path

from plat.views import login_view

urlpatterns = [
    path('', login_view),  # 登录首页
]
