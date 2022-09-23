from django.shortcuts import render


def performance_main_view(request):
    """性能测试平台首页"""
    return render(request, "performance_main.html")
