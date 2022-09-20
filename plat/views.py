from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from plat.models import User
from plat.serializers import UserDetailSerialize
from django.views.generic import View
from rest_framework.views import APIView
from rest_framework.response import Response


def login_view(request):
    """登录试图函数"""
    return render(request, 'plat/login.html')


def login(request):
    """用户登录"""
    count = request.POST.get("count")
    password = request.POST.get("password")
    if User.objects.get("count") == count and User.objects.get("password") == password:
        return HttpResponse("登录成功")  # 跳转测试平台主页
    else:
        return HttpResponse("没有该用户，去注册吧")


def register_view(request):
    """注册试图函数"""
    return render(request, 'plat/register.html')


class Register(View):
    """用户账号增删改"""
    def post(self, request):
        count_list = []
        count = request.POST.get("count")
        password = request.POST.get("password")
        re_password = request.POST.get("re_password")
        count_list_query = User.objects.filter(count=count)
        count_list_serializer = UserDetailSerialize(count_list_query, many=True)
        count_dict_query = count_list_serializer.data
        for i in count_dict_query:
            print(count_list.append(i["count"]))
        print(f"账号：{count} ,密码：{password},确认密码：{re_password}")
        print(f"数据库中的账号情况：{count_list}")
        print(len(str(count)))
        if len(str(count)) == 0:
            return HttpResponse("账号为不能不填写")
        if len(str(password)) == 0:
            return HttpResponse("密码不能不填写")
        if len(str(re_password)) == 0:
            return HttpResponse("确认密码不能不填写")
        if password != re_password:
            return HttpResponse("确认密码与密码不相同")
        if len(str(count)) >= 20 or len(str(password)) >= 20:
            print("账号密码太长了，不得长于20个字符")
            return render(request, "plat/register.html")
        if count in count_list:
            print("账号已经存在")
            return render(request, "plat/login.html")
        else:
            User.objects.create(
                count=count,
                password=password
            )
            return HttpResponse("创建成功")

    def delete(self, request):
        count = request.POST.get("count")
        User.objects.filter(count=count).delete()  # 直接从模型类删除
        return HttpResponse("已经删除该账号数据")
