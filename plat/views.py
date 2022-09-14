from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
# Create your views here.
from plat.models import User


def login_view(request):
    """登录试图函数"""
    return render(request, 'plat/login.html')


def login(request):
    """用户登录"""
    pass


def register_view(request):
    """注册试图函数"""
    return render(request, 'plat/register.html')


def register(request):
    """用户注册"""
    pass
