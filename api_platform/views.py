from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.


def test_platform(request):
    """测试试图函数"""
    return render(request, "api_platform/api_main.html")
