from django.shortcuts import render
from django.http import HttpResponse


def api_main_view(request):
    """测试试图函数"""
    return render(request, "api_platform/api_main.html")


def api_manage_view(request):
    """接口管理页面"""
    return render(request, "api_platform/api_manage.html")


def case_manage_view(request):
    """用例管理页面"""
    return render(request, "api_platform/case_manage.html")


def ci_di(request):
    """持续集成界面"""
    return render(request, "api_platform/ci_di.html")
