from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View


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


class SetApi(View):
    """接口操作接口"""
    def put(self, request):
        api = request.Get("")

    def get(self, request):
        key = request.GET.get("key")
        message = dict()

    def post(self, request):
        body = request.body
        print(f"传递的参数是{body}")

    def delete(self, request):
        pass


class CaseApi(View):
    """用例操作接口"""

    def put(self, request):
        pass

    def get(self, request):
        pass

    def post(self, request):
        pass

    def delete(self, request):
        pass
