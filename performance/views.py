from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
import queue
import json
import time


def performance_main_view(request):
    """性能测试主页"""
    return render(request, "performance/performance_main.html")
