from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
# Create your views here.


def test_view(request):
    """测试试图函数"""
    return render(request, 'plat/login.html')

