import json


from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.db.models import Count, Q
from api_platform.models import Api, Case


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
    print("接口管理页面")
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
        """更新接口"""
        api_data = request.body.decode('utf-8')
        data = json.loads(api_data)
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
        return JsonResponse({'message':"Update API successfully"}, status=200)


    def get(self, request):
        """获取接口"""
        key = request.GET.get("key")
        message = dict()

    def post(self, request):
        """创建接口"""
        try:
            data = json.loads(request.body)
            api_hoster = data.get("api_hoster")
            api_name = data.get("api_name")
            api_url = data.get("api_url")
            api_path = data.get("api_path")
            api_method = data.get("api_method", "GET")
            api_header = data.get("api_header")
            api_body = data.get("api_body")
            api_params = data.get("api_params")
            api_desc = data.get("api_desc")
            api = Api(
                name=api_name,
                hoster_name = api_hoster,
                base_url = api_url,
                api_path = api_path,
                method = api_method,
                headers = api_header,
                body = api_body,
                params = api_params,
                desc = api_desc,
                publish = False  # 默认不发布
            )
            api.save()
            return JsonResponse({'message': 'Create API successfully'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    def delete(self, request):
        """删除接口"""
        try:
            api_id = request.GET.get("api_id")
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
