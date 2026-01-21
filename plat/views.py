import random
import time

from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from plat.models import User
from plat.serializers import UserDetailSerialize
from django.views.generic import View
from functools import wraps


def login_view(request):
    """登录试图函数"""
    return render(request, 'plat/login.html')


def login(request):
    """用户登录"""
    count_ = request.POST.get("count")
    password = request.POST.get("password")
    
    try:
        user = User.objects.get(count=count_)
    except User.DoesNotExist:
        error_data = {"error_info": "没有该账号，请先注册"}
        return render(request, "plat/alert.html", context=error_data)
    
    if password != user.password:
        return HttpResponse("密码不正确")
    else:
        request.session["user_id"] = user.uid
        request.session["user_count"] = user.count
        request.session["logged_in"] = True  # 标记已登录
        print("登录成功")
        return redirect("main_view")


def custom_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('logged_in'):
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return wrapper


@custom_login_required
def main_view(request):
    """登录后的平台主页"""
    # 也可以检查所有 session 数据
    # for key, value in request.session.items():
    #     print(f"Session - {key}: {value}")
    return render(request, "plat/main.html")


def register_view(request):
    """注册试图函数"""
    return render(request, 'plat/register.html')


class Register(View):
    """用户账号增删改"""
    def post(self, request):
        count_list = []
        error_data = dict()
        count = request.POST.get("count")
        password = request.POST.get("password")
        re_password = request.POST.get("re_password")
        count_list_query = User.objects.filter(count=count)
        count_list_serializer = UserDetailSerialize(count_list_query, many=True)
        count_dict_query = count_list_serializer.data
        for i in count_dict_query:
            count_list.append(i["count"])
        # print(f"账号：{count} ,密码：{password},确认密码：{re_password}")
        # print(f"数据库中的账号情况：{count_list}")
        # print(len(str(count)))
        if len(str(count)) == 0:
            error_data["error_info"] = "账号不能不填写"
            return render(request, "plat/alert.html", context=error_data)
        if len(str(password)) == 0:
            error_data["error_info"] = "密码不能不填写"
            return render(request, "plat/alert.html", context=error_data)
        if len(str(re_password)) == 0:
            error_data["error_info"] = "确认密码不能不填写"
            return render(request, "plat/alert.html", context=error_data)
        if password != re_password:
            error_data["error_info"] = "确认密码与密码不相同"
            return render(request, "plat/alert.html", context=error_data)
        if len(str(count)) >= 20 or len(str(password)) >= 20:
            error_data["error_info"] = "账号密码太长了，不得长于20个字符"
            return render(request, "plat/alert.html", context=error_data)
        if count in count_list:
            user = User.objects.get(count=count)
            user.password = password
            user.save()
            return render(request, 'plat/login.html')  # todo:密码已经修改，请查看提示
        else:
            timestamp = int(time.time())
            random_numbner = random.randint(0, 9999)
            uid = timestamp*10 + random_numbner
            print(f"生成的uid:{uid}")
            User.objects.create(
                uid=str(uid),
                count=count,
                password=password
            )
            return HttpResponse("创建成功")

    def get(self, request):
        count = request.GET.get("count")
        User.objects.filter(count=count).delete()  # 直接从模型类删除
        return HttpResponse("已经删除该账号数据")
