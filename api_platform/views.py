import json


from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.db.models import Count, Q
from api_platform.models import Api, Case
from plat.models import User
from django.views.decorators.csrf import csrf_exempt


def api_main_view(request):
    """测试试图函数"""
    api_counts = Api.objects.aggregate(
        all_api_count=Count('id'),
        publish_api_count=Count('id', filter=Q(publish=True))
    )
    case_counts = Case.objects.aggregate(
        all_case_count=Count('id'),
        publish_case_count=Count('id', filter=Q(publish=True))
    )
    all_api_count = api_counts['all_api_count']
    all_case_count = case_counts['all_case_count']
    publish_api_count = api_counts['publish_api_count']
    publish_case_count = case_counts['publish_case_count']
    if not all_api_count:
        all_api_count = 10
    if not all_case_count:
        all_case_count = 10
    if not publish_api_count:
        publish_api_count = 5
    if not publish_case_count:
        publish_case_count = 5
    data = {
        "all_api_count": all_api_count,
        "all_case_count": all_case_count,
        "publish_api_count": publish_api_count,
        "publish_case_count": publish_case_count
    }
    return render(request, "api_platform/api_main.html", context=data)


def api_manage_view(request):
    """接口管理页面"""
    return render(request, "api_platform/api_manage.html")


def case_manage_view(request):
    """用例管理页面"""
    return render(request, "api_platform/case_manage.html")


def ci_di(request):
    """持续集成界面"""
    return render(request, "api_platform/ci_di.html")


def post_api(request):
    """创建接口"""
    try:
        # 查看请求携带的cookies
        data = json.loads(request.body)
        acount = request.session.get("count")
        print(f"账号：{acount}")
        user_name = User.objects.get(count=acount).name
        api_hoster = user_name
        api_name = data.get("api_name")
        api_url = data.get("api_url")
        api_path = data.get("api_path")
        api_method = data.get("api_method", "GET")
        api_header = data.get("api_header")
        api_body = data.get("api_body")
        api_params = data.get("api_params")
        api_desc = data.get("api_desc")
        # 检查数据库中是否存在相同的接口
        if Api.objects.filter(api_path=api_path).exists() and Api.objects.filter(
                base_url=api_url).exists() and Api.objects.filter(method=api_method).exists() and Api.objects.filter(
                headers=api_header).exists() and Api.objects.filter(body=api_body).exists() and Api.objects.filter(
                params=api_params).exists():
            return JsonResponse({'message': 'API already exists'}, status=400)
        api = Api(
            name=api_name,
            hoster_name=api_hoster,
            base_url=api_url,
            api_path=api_path,
            method=api_method,
            headers=api_header,
            body=api_body,
            params=api_params,
            desc=api_desc,
            publish=False  # 默认不发布
        )
        api.save()
        return JsonResponse({'message': 'Create API successfully'}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


def put_api(request):
    """更新接口"""
    data = json.loads(request.body)
    print(f"传递的参数是:{data}")
    api_id = data.get("api_id")
    if not api_id:
        return JsonResponse({'message': 'Invalid API ID'}, status=400)
    try:
        api_data = Api.objects.get(id=api_id)
    except Api.DoesNotExist:
        return JsonResponse({'message': 'API not found'}, status=404)
    for key, value in data.items():
        if key == "api_id":
            continue
        if hasattr(api_data, key):
            setattr(api_data, key, value)
    api_data.save()
    return JsonResponse({'message': "Update API successfully", "data": api_data.to_dict()}, status=200)


@csrf_exempt
def get_api(request):
    """获取接口"""
    # 打印请求头
    try:
        query_params = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON format'}, status=400)
    acount = request.session.get("count")
    print(f"cookies的值：{acount}")
    # 初始化查询集
    apis = Api.objects.all()
    # 处理查询参数
    query = Q()
    for key, value_list in query_params.items():
        if key in [field.name for field in Api._meta.fields]:
            for value in value_list:
                field_name = f"{key}__icontains"
                query |= Q(**{field_name: value})
    apis = apis.filter(query)
    if not apis:
        return JsonResponse({'message': 'API not found'}, status=404)
    # 将查询结果转换为字典列表
    data_list = []
    for api in apis:
        api_dict = api.to_dict()
        api_dict['id'] = api.id  # 手动添加ID字段
        data_list.append(api_dict)
    data = {
        "data": data_list
    }
    print(data)
    return JsonResponse(data, status=200)


def delete_api(request):
    """删除接口"""
    try:
        query_params = json.loads(request.body)
        api_id = query_params.get("api_id")
        if not api_id:
            return JsonResponse({'message': 'Invalid API ID'}, status=400)
        api = Api.objects.get(id=api_id)
        if not api:
            return JsonResponse({'message': 'API not found'}, status=404)
        api.delete()
        return JsonResponse({'message': 'Delete API successfully'}, status=200)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)


class SetCase(View):
    """用例操作接口"""

    def put(self, request):
        pass

    def get(self, request):
        pass

    def post(self, request):
        pass

    def delete(self, request):
        pass
